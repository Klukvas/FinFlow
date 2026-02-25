from __future__ import annotations

import logging
import secrets
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import CreatePaymentRequest, CreatePaymentResponse, PaymentOut, RefundRequest, RefundResponse
from ..config import settings
from ..utils.errors import AuthError
from ..utils.idempotency import (
    check_idempotency,
    store_idempotency,
    compute_request_hash,
    get_idempotency_key,
)

logger = logging.getLogger("payment_service.internal_router")

router = APIRouter()


def verify_internal_token(x_internal_token: str = Header(alias="X-Internal-Token")) -> None:
    """Verify internal service token"""
    if not x_internal_token or not secrets.compare_digest(x_internal_token, settings.internal_secret_token):
        raise AuthError(
            "Invalid internal token",
            error_code="@payment_service/INVALID_INTERNAL_TOKEN",
        )


@router.post(
    "/internal/payments",
    response_model=CreatePaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_internal(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
):
    """
    Internal endpoint for other services to create payments
    
    Requires X-Internal-Token header.
    """
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
        provider_form_fields=payment.provider_payload,  # Return form fields
        created_at=payment.created_at,
    )

    logger.info(
        f"Payment created via internal API: {payment.id}",
        extra={
            "payment_id": str(payment.id),
            "user_id": str(request.user_id),
            "amount": str(request.amount),
        },
    )

    return response


@router.get("/internal/payments/{payment_id}", response_model=PaymentOut)
async def get_payment_internal(
    payment_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
):
    """
    Get payment details by ID (internal)
    
    Requires X-Internal-Token header.
    No user ownership check.
    """
    service = PaymentService(db)
    payment = service.payment_repo.get_by_id_or_raise(payment_id)
    return PaymentOut.model_validate(payment)


@router.post("/internal/payments:recurring", response_model=CreatePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_payment_internal(
    request: dict,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
):
    """
    Create and execute recurring payment using stored token
    
    Requires X-Internal-Token header.
    
    Request body:
    {
        "user_id": "string",
        "subscription_id": int,
        "plan_code": "string",
        "amount": "decimal_string",
        "currency": "string",
        "recurring_token": "string"
    }
    """
    service = PaymentService(db)
    
    try:
        payment = await service.create_recurring_payment(
            user_id=request["user_id"],
            subscription_id=request.get("subscription_id"),
            plan_code=request["plan_code"],
            amount=request["amount"],
            currency=request["currency"],
            recurring_token=request["recurring_token"],
        )
        
        response = CreatePaymentResponse(
            payment_id=payment.id,
            order_reference=payment.order_reference,
            provider=payment.provider,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            payment_url=None,  # No URL for recurring
            provider_form_fields=None,
            created_at=payment.created_at,
        )
        
        logger.info(
            f"Recurring payment created: {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "user_id": request["user_id"],
                "subscription_id": request.get("subscription_id"),
                "status": payment.status.value,
            },
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to create recurring payment: {e}",
            extra={
                "user_id": request.get("user_id"),
                "error": str(e),
            },
        )
        raise


@router.post("/internal/payments/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment_internal(
    payment_id: UUID,
    request: RefundRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
):
    """
    Request refund for a payment (internal)

    Requires X-Internal-Token header.
    Calls Paddle Adjustments API to issue refund.
    Supports idempotency via ``Idempotency-Key`` header to prevent double refunds.
    """
    # Check idempotency to prevent double refund
    request_hash = ""
    if idempotency_key:
        request_hash = compute_request_hash({
            "payment_id": str(payment_id),
            **request.model_dump(mode="json"),
        })
        cached_response = check_idempotency(db, idempotency_key, "refund_payment", request_hash)
        if cached_response:
            return cached_response

    service = PaymentService(db)
    payment = service.payment_repo.get_by_id_or_raise(payment_id)

    logger.info(
        f"Refund requested for payment {payment_id}",
        extra={
            "payment_id": str(payment_id),
            "amount": str(request.amount) if request.amount else "full",
            "reason": request.reason,
        },
    )

    payment = await service.process_refund(
        payment=payment,
        amount=request.amount,
        reason=request.reason,
    )

    response = RefundResponse(
        payment_id=payment.id,
        status=payment.status,
        refunded_amount=request.amount or payment.amount,
        refunded_at=payment.refunded_at,
    )

    # Store idempotency key to prevent duplicate refunds
    if idempotency_key:
        store_idempotency(
            db, idempotency_key, "refund_payment",
            request_hash, response.model_dump(mode="json"), "200",
        )

    return response
