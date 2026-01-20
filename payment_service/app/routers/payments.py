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
from ..utils.errors import AuthError, NotFoundError, ValidationError
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


@router.get("/payments/{payment_id}/redirect")
async def redirect_to_payment_provider(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    """
    Generate HTML page that auto-submits payment form to WayForPay
    
    This is a helper endpoint for frontend to redirect user to payment provider.
    """
    from fastapi.responses import HTMLResponse
    
    service = PaymentService(db)
    payment = service.payment_repo.get_by_id_or_raise(payment_id)
    
    # Verify user owns the payment
    if str(payment.user_id) != str(current_user.user_id):
        raise AuthError(
            "Cannot access another user's payment",
            error_code="@payment_service/UNAUTHORIZED_ACCESS",
        )
    
    if not payment.provider_payment_url or not payment.provider_payload:
        raise ValidationError(
            "Payment provider data not available",
            error_code="@payment_service/PAYMENT_DATA_MISSING",
        )
    
    # Generate HTML form that auto-submits
    form_fields = ""
    for key, value in payment.provider_payload.items():
        if isinstance(value, list):
            for item in value:
                form_fields += f'<input type="hidden" name="{key}[]" value="{item}">\n'
        else:
            form_fields += f'<input type="hidden" name="{key}" value="{value}">\n'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to Payment...</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Redirecting to Payment Gateway...</h2>
            <div class="spinner"></div>
            <p>Please wait, you will be redirected shortly.</p>
        </div>
        <form id="paymentForm" method="POST" action="{payment.provider_payment_url}">
            {form_fields}
        </form>
        <script>
            // Auto-submit form after a brief delay
            setTimeout(function() {{
                document.getElementById('paymentForm').submit();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


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
