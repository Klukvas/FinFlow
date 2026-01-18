from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import WebhookWayForPayRequest
from ..utils.errors import ValidationError, NotFoundError

logger = logging.getLogger("payment_service.webhooks_router")

router = APIRouter()


@router.post("/webhooks/wayforpay")
async def wayforpay_webhook(
    callback: WebhookWayForPayRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    WayForPay webhook endpoint
    
    No JWT required - authentication via signature verification.
    Returns 200 OK for all valid requests to prevent provider retries.
    """
    logger.info(
        f"Received WayForPay webhook for order {callback.orderReference}",
        extra={
            "order_reference": callback.orderReference,
            "transaction_status": callback.transactionStatus,
            "merchant_account": callback.merchantAccount,
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
