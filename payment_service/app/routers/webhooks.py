from __future__ import annotations

import logging
import json
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError as PydanticValidationError

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import WebhookWayForPayRequest
from ..utils.errors import ValidationError, NotFoundError
from ..config import settings

logger = logging.getLogger("payment_service.webhooks_router")

router = APIRouter()


@router.post("/payment/return")
@router.get("/payment/return")
async def payment_return_redirect(request: Request):
    """
    Handle WayForPay return redirect (POST or GET).
    Redirects to frontend payment return page.
    """
    # Get query params or form data
    params = dict(request.query_params)
    
    if request.method == "POST":
        try:
            form_data = await request.form()
            params.update(dict(form_data))
        except:
            pass
    
    logger.info(f"Payment return redirect with params: {params}")
    
    # Build redirect URL to frontend
    frontend_url = settings.wayforpay_return_url
    
    # Add params as query string
    if params:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        redirect_url = f"{frontend_url}?{query_string}"
    else:
        redirect_url = frontend_url
    
    logger.info(f"Redirecting to: {redirect_url}")
    
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/webhooks/wayforpay")
async def wayforpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    WayForPay webhook endpoint
    
    No JWT required - authentication via signature verification.
    Returns 200 OK for all valid requests to prevent provider retries.
    """
    # Read raw body first for debugging
    raw_body = await request.body()
    logger.info(f"Received WayForPay webhook raw body: {raw_body.decode('utf-8', errors='replace')}")
    
    # Try to parse as JSON
    try:
        body_json = json.loads(raw_body)
        logger.info(f"Parsed webhook JSON: {json.dumps(body_json, indent=2)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook body as JSON: {e}")
        return JSONResponse(
            content={"status": "decline", "reason": "Invalid JSON"},
            status_code=status.HTTP_200_OK
        )
    
    # Validate with Pydantic
    try:
        callback = WebhookWayForPayRequest(**body_json)
    except PydanticValidationError as e:
        logger.error(f"Webhook validation error: {e.errors()}")
        return JSONResponse(
            content={"status": "decline", "reason": "Validation error", "errors": str(e.errors())},
            status_code=status.HTTP_200_OK
        )
    
    logger.info(
        f"Received WayForPay webhook for order {callback.orderReference}",
        extra={
            "order_reference": callback.orderReference,
            "transaction_status": callback.transactionStatus,
            "merchant_account": callback.merchantAccount,
            "has_rec_token": callback.recToken is not None,
            "rec_token_preview": callback.recToken[:20] + "..." if callback.recToken and len(callback.recToken) > 20 else callback.recToken,
        },
    )

    try:
        service = PaymentService(db)
        payment = await service.process_wayforpay_callback(callback)

        logger.info(
            f"Successfully processed webhook for payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": callback.orderReference,
                "status": payment.status.value,
            },
        )

        # Always return 200 OK with accept/decline response
        response_data = {
            "orderReference": callback.orderReference,
            "status": "accept",
            "time": int(payment.updated_at.timestamp()),
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

    except ValidationError as e:
        # Invalid signature or validation error
        logger.warning(
            f"Webhook validation error: {e.message}",
            extra={
                "order_reference": callback.orderReference,
                "error_code": e.error_code,
            },
        )

        # Return 200 but with decline status
        response_data = {
            "orderReference": callback.orderReference,
            "status": "decline",
            "time": 0,
        }
        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

    except NotFoundError as e:
        # Payment not found
        logger.error(
            f"Payment not found for webhook: {e.message}",
            extra={
                "order_reference": callback.orderReference,
                "error_code": e.error_code,
            },
        )

        response_data = {
            "orderReference": callback.orderReference,
            "status": "decline",
            "time": 0,
        }
        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

    except Exception as e:
        # Unexpected error - still return 200 to prevent infinite retries
        logger.error(
            f"Unexpected error processing webhook: {e}",
            extra={
                "order_reference": callback.orderReference,
                "error": str(e),
            },
            exc_info=True,
        )

        response_data = {
            "orderReference": callback.orderReference,
            "status": "decline",
            "time": 0,
        }
        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
