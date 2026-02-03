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
from ..config import settings

logger = logging.getLogger("payment_service.payments_router")

router = APIRouter()


@router.get("/config/status")
async def get_payment_status():
    """
    Get payment service status and feature flags.
    Public endpoint - no authentication required.
    """
    return {
        "payments_enabled": settings.payments_enabled,
        "service_status": "operational",
    }


@router.get("/config/check")
async def check_wayforpay_config():
    """
    Check WayForPay configuration status.
    Useful for debugging payment form issues.
    
    NOTE: Does not expose secret values, only validation status.
    """
    # Check for default/test credentials
    is_using_test_merchant = (
        not settings.wayforpay_merchant_account or 
        settings.wayforpay_merchant_account == "test_merch_n1"
    )
    is_using_test_secret = (
        not settings.wayforpay_merchant_secret_key or 
        settings.wayforpay_merchant_secret_key == "flk3409refn54t54t*FNJRET"
    )
    is_using_test_domain = (
        not settings.wayforpay_merchant_domain or 
        settings.wayforpay_merchant_domain == "www.market.ua"
    )
    
    has_callback_url = bool(settings.wayforpay_callback_url)
    has_return_url = bool(settings.wayforpay_return_url)
    
    # Overall configuration status
    is_production_ready = not (
        is_using_test_merchant or 
        is_using_test_secret or 
        is_using_test_domain
    ) and has_callback_url and has_return_url
    
    config_status = {
        "status": "ok" if is_production_ready else "configuration_needed",
        "checks": {
            "merchant_account": {
                "configured": not is_using_test_merchant,
                "value_preview": settings.wayforpay_merchant_account[:10] + "..." if settings.wayforpay_merchant_account and len(settings.wayforpay_merchant_account) > 10 else settings.wayforpay_merchant_account,
                "warning": "Using default test credentials - will not work!" if is_using_test_merchant else None,
            },
            "merchant_secret_key": {
                "configured": not is_using_test_secret,
                "has_value": bool(settings.wayforpay_merchant_secret_key),
                "length": len(settings.wayforpay_merchant_secret_key) if settings.wayforpay_merchant_secret_key else 0,
                "warning": "Using default test credentials - will not work!" if is_using_test_secret else None,
            },
            "merchant_domain": {
                "configured": not is_using_test_domain,
                "value": settings.wayforpay_merchant_domain,
                "warning": "Using default test domain - must match your WayForPay merchant domain!" if is_using_test_domain else None,
            },
            "callback_url": {
                "configured": has_callback_url,
                "value": settings.wayforpay_callback_url,
                "is_https": settings.wayforpay_callback_url.startswith("https://") if has_callback_url else False,
                "warning": "Not configured!" if not has_callback_url else ("Must be HTTPS for webhooks to work!" if not settings.wayforpay_callback_url.startswith("https://") else None),
            },
            "return_url": {
                "configured": has_return_url,
                "value": settings.wayforpay_return_url,
                "warning": "Not configured!" if not has_return_url else None,
            },
        },
        "production_ready": is_production_ready,
        "documentation": "See WAYFORPAY_SETUP.md for configuration instructions",
    }
    
    if not is_production_ready:
        logger.warning(
            "WayForPay configuration is incomplete or using test credentials!",
            extra={
                "using_test_merchant": is_using_test_merchant,
                "using_test_secret": is_using_test_secret,
                "using_test_domain": is_using_test_domain,
                "has_callback_url": has_callback_url,
                "has_return_url": has_return_url,
            }
        )
    
    return config_status


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
            "order_reference": payment.order_reference,
            "payment_url_in_response": response.payment_url,
            "has_form_fields_in_response": bool(response.provider_form_fields),
            "form_fields_count": len(response.provider_form_fields) if response.provider_form_fields else 0,
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
