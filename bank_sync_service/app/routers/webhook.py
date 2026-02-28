from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class MonobankWebhookData(BaseModel):
    """Expected shape of Monobank webhook POST body."""
    type: str
    data: dict


@router.get("/monobank")
async def monobank_webhook_verify():
    """Monobank sends GET to verify webhook URL exists."""
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.post("/monobank")
async def monobank_webhook_receive(request: Request):
    """Receive realtime transaction push from Monobank.

    Monobank sends a POST with transaction data when a new transaction occurs.
    We log it for now — full processing can be added when webhook URL is configured.

    NOTE: Monobank does not sign webhooks, so we cannot verify the sender.
    When implementing full processing, consider IP allowlisting or other safeguards.
    """
    try:
        body = await request.json()
        MonobankWebhookData(**body)
    except (ValueError, ValidationError):
        logger.warning("Received invalid Monobank webhook payload")
        return JSONResponse(status_code=200, content={"status": "invalid"})

    logger.info(
        "Received Monobank webhook",
        extra={"webhook_type": body.get("type")},
    )

    # TODO: In future, process webhook data:
    # 1. Find connection by account ID
    # 2. Deduplicate
    # 3. Create expense/income

    return JSONResponse(status_code=200, content={"status": "received"})
