from __future__ import annotations

import logging
import json
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError as PydanticValidationError

from ..database import get_db
from ..services.payment_service import PaymentService
from ..clients.paddle_client import PaddleClient
from ..schemas.payment import PaddleWebhookEvent

logger = logging.getLogger("payment_service.webhooks_router")

router = APIRouter()


@router.post("/webhooks/paddle")
async def paddle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Paddle Billing webhook endpoint.

    No JWT required -- authentication is via Paddle signature verification.
    Always returns 200 OK to prevent Paddle retry storms.

    Paddle sends a ``Paddle-Signature`` header containing ``ts=<unix>;h1=<hmac>``.
    The body is a JSON envelope with ``event_id``, ``event_type``, ``occurred_at``,
    ``notification_id``, and ``data``.
    """
    # Read raw body for signature verification
    raw_body = await request.body()

    # Verify signature
    paddle_signature = request.headers.get("Paddle-Signature", "")
    paddle_client = PaddleClient()

    if not paddle_signature:
        logger.warning("Paddle webhook received without Paddle-Signature header")
        return JSONResponse(
            content={"status": "error", "reason": "Missing Paddle-Signature header"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    signature_valid = paddle_client.verify_webhook_signature(raw_body, paddle_signature)
    if not signature_valid:
        logger.warning(
            "Paddle webhook signature verification failed",
            extra={"signature_header_preview": paddle_signature[:60]},
        )
        return JSONResponse(
            content={"status": "error", "reason": "Invalid signature"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Parse JSON body
    try:
        body_json = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse Paddle webhook body as JSON: {exc}")
        return JSONResponse(
            content={"status": "error", "reason": "Invalid JSON"},
            status_code=status.HTTP_200_OK,
        )

    # Validate with Pydantic
    try:
        event = PaddleWebhookEvent(**body_json)
    except PydanticValidationError as exc:
        logger.error(
            "Paddle webhook validation error",
            extra={"errors": str(exc.errors())},
        )
        return JSONResponse(
            content={"status": "error", "reason": "Validation error"},
            status_code=status.HTTP_200_OK,
        )

    logger.info(
        f"Received Paddle webhook: {event.event_type}",
        extra={
            "event_id": event.event_id,
            "event_type": event.event_type,
            "occurred_at": event.occurred_at,
            "notification_id": event.notification_id,
        },
    )

    # Process event
    try:
        service = PaymentService(db)
        payment = await service.process_paddle_webhook(event)

        if payment:
            logger.info(
                f"Paddle webhook processed successfully for payment {payment.id}",
                extra={
                    "payment_id": str(payment.id),
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "payment_status": payment.status.value,
                },
            )
        else:
            logger.info(
                "Paddle webhook processed (no payment affected or duplicate)",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                },
            )

        return JSONResponse(
            content={"status": "ok", "event_id": event.event_id},
            status_code=status.HTTP_200_OK,
        )

    except Exception as exc:
        # Always return 200 to prevent Paddle infinite retries
        logger.error(
            f"Error processing Paddle webhook: {exc}",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "error": str(exc),
            },
            exc_info=True,
        )

        return JSONResponse(
            content={"status": "error", "event_id": event.event_id},
            status_code=status.HTTP_200_OK,
        )
