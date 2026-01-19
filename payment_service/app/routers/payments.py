from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import CreatePaymentRequest, CreatePaymentResponse, PaymentOut
from ..utils.jwt import get_current_user, JWTPayload
from ..utils.errors import AuthError, NotFoundError
from ..utils.idempotency import (
    check_idempotency,
    store_idempotency,
    compute_request_hash,
    get_idempotency_key,
)

logger = logging.getLogger("payment_service.payments_router")

router = APIRouter()


@router.post("/payments", response_model=CreatePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
):
    """
    Create a new payment
    
    Requires JWT authentication.
    Supports idempotency via Idempotency-Key header.
    """
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

    # Create payment
    service = PaymentService(db)
    payment = service.create_payment(request)

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

    # Store idempotency key
    if idempotency_key:
        store_idempotency(
            db,
            idempotency_key,
            "create_payment",
            request_hash,
            response.model_dump(mode="json"),
            "201",
        )

    logger.info(
        f"Payment created via API: {payment.id}",
        extra={
            "payment_id": str(payment.id),
            "user_id": str(current_user.user_id),
            "amount": str(payment.amount),
        },
    )

    return response


@router.get("/payments/by-order/{order_reference}", response_model=PaymentOut)
async def get_payment_by_order_reference(
    order_reference: str,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """
    Get payment details by order reference
    
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
    """
    Get payment details by ID
    
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
    """
    List user's payments
    
    Requires JWT authentication.
    Returns payments for the authenticated user.
    """
    service = PaymentService(db)
    payments = service.payment_repo.get_by_user_id(
        user_id=current_user.user_id,
        limit=min(limit, 100),  # Cap at 100
        offset=offset,
    )

    return [PaymentOut.model_validate(p) for p in payments]
