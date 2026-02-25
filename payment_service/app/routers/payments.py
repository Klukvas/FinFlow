from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    ChangePlanRequest,
    ChangePlanResponse,
    PaymentOut,
)
from ..utils.jwt import get_current_user, JWTPayload
from ..utils.errors import AuthError, ValidationError
from ..utils.idempotency import (
    check_idempotency,
    store_idempotency,
    compute_request_hash,
    get_idempotency_key,
)
from ..utils.rate_limit import require_payment_rate_limit
from ..config import settings

logger = logging.getLogger("payment_service.payments_router")

router = APIRouter()


@router.get("/config/status")
def get_payment_status():
    """Get payment service status and feature flags.

    Public endpoint -- no authentication required.
    """
    return {
        "payments_enabled": settings.payments_enabled,
        "service_status": "operational",
    }


@router.get("/config/check")
def check_paddle_config():
    """Check Paddle Billing configuration status.

    Useful for verifying that all required environment variables
    are set before going live.  Does not expose secret values.
    """
    is_production_ready = bool(
        settings.paddle_api_key
        and settings.paddle_webhook_secret
        and settings.paddle_environment == "production"
    )

    config_status = {
        "status": "ok" if settings.paddle_api_key else "configuration_needed",
        "checks": {
            "api_key": {"configured": bool(settings.paddle_api_key)},
            "webhook_secret": {"configured": bool(settings.paddle_webhook_secret)},
            "environment": {"value": settings.paddle_environment},
            "success_url": {"configured": bool(settings.paddle_success_url)},
        },
        "production_ready": is_production_ready,
    }

    if not settings.paddle_api_key:
        logger.warning(
            "Paddle configuration incomplete: API key not set",
            extra={
                "has_api_key": bool(settings.paddle_api_key),
                "has_webhook_secret": bool(settings.paddle_webhook_secret),
                "environment": settings.paddle_environment,
            },
        )

    return config_status


@router.post("/payments", response_model=CreatePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
    _rate_limit: None = Depends(require_payment_rate_limit),
):
    """Create a new payment via Paddle checkout.

    Requires JWT authentication.
    Supports idempotency via ``Idempotency-Key`` header.
    """
    # Check if payments are enabled
    if not settings.payments_enabled:
        raise ValidationError(
            "Payment processing is temporarily disabled. Please contact support for more information.",
            error_code="@payment_service/PAYMENTS_DISABLED",
        )

    # Verify user owns the payment request
    if str(request.user_id) != str(current_user.user_id):
        raise AuthError(
            "Cannot create payment for another user",
            error_code="@payment_service/UNAUTHORIZED_USER",
        )

    # Check idempotency
    if idempotency_key:
        request_hash = compute_request_hash(request.model_dump(mode="json"))
        cached_response = check_idempotency(db, idempotency_key, "create_payment", request_hash)
        if cached_response:
            return cached_response

    # Create payment (async -- calls Paddle API)
    service = PaymentService(db)
    payment = await service.create_payment(request)

    response = CreatePaymentResponse(
        payment_id=payment.id,
        order_reference=payment.order_reference,
        provider=payment.provider,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        payment_url=payment.provider_payment_url,
        checkout_url=payment.provider_payment_url,
        transaction_id=payment.paddle_transaction_id,
        provider_form_fields=payment.provider_payload,
        created_at=payment.created_at,
    )

    # Store idempotency key INSIDE transaction (before returning response)
    # to prevent duplicates if server crashes between response and storage
    if idempotency_key:
        store_idempotency(
            db,
            idempotency_key,
            "create_payment",
            request_hash,
            response.model_dump(mode="json"),
            "201",
            auto_commit=False,
        )
        db.commit()

    logger.info(
        f"Payment created via API: {payment.id}",
        extra={
            "payment_id": str(payment.id),
            "user_id": str(current_user.user_id),
            "amount": str(payment.amount),
            "order_reference": payment.order_reference,
            "checkout_url_present": bool(response.checkout_url),
        },
    )

    return response


@router.post("/payments/change-plan", response_model=ChangePlanResponse)
async def change_plan(
    request: ChangePlanRequest,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """Change subscription plan (upgrade or downgrade) via Paddle API.

    Requires JWT authentication.
    The user must own the subscription being changed.
    """
    if not settings.payments_enabled:
        raise ValidationError(
            "Payment processing is temporarily disabled.",
            error_code="@payment_service/PAYMENTS_DISABLED",
        )

    if str(request.user_id) != str(current_user.user_id):
        raise AuthError(
            "Cannot change plan for another user",
            error_code="@payment_service/UNAUTHORIZED_USER",
        )

    service = PaymentService(db)
    result = await service.change_subscription_plan(request)

    logger.info(
        "Plan changed via API",
        extra={
            "user_id": str(current_user.user_id),
            "old_plan_code": result.get("old_plan_code"),
            "new_plan_code": result["new_plan_code"],
            "paddle_subscription_id": result["paddle_subscription_id"],
        },
    )

    return ChangePlanResponse(**result)


@router.get("/payments/by-order/{order_reference}", response_model=PaymentOut)
async def get_payment_by_order_reference(
    order_reference: str,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """Get payment details by order reference.

    Requires JWT authentication.
    Users can only access their own payments.
    """
    service = PaymentService(db)
    payment = service.payment_repo.get_by_order_reference_or_raise(order_reference)

    # Verify user owns the payment
    if str(payment.user_id) != str(current_user.user_id):
        raise AuthError(
            "Cannot access another user's payment",
            error_code="@payment_service/UNAUTHORIZED_ACCESS",
        )

    return PaymentOut.model_validate(payment)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """Get payment details by ID.

    Requires JWT authentication.
    Users can only access their own payments.
    """
    service = PaymentService(db)
    payment = service.payment_repo.get_by_id_or_raise(payment_id)

    # Verify user owns the payment
    if str(payment.user_id) != str(current_user.user_id):
        raise AuthError(
            "Cannot access another user's payment",
            error_code="@payment_service/UNAUTHORIZED_ACCESS",
        )

    return PaymentOut.model_validate(payment)


@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """List the authenticated user's payments.

    Requires JWT authentication.
    Returns payments for the authenticated user only.
    """
    service = PaymentService(db)
    payments = service.payment_repo.get_by_user_id(
        user_id=current_user.user_id,
        limit=min(limit, 100),  # Cap at 100
        offset=offset,
    )

    return [PaymentOut.model_validate(p) for p in payments]
