import html
import re
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/support", tags=["Support"])

# ---------------------------------------------------------------------------
# Rate limiting (in-memory, 1 message per minute per user)
# ---------------------------------------------------------------------------
_rate_limit_store: dict[int, float] = {}
RATE_LIMIT_SECONDS = 60


def _check_rate_limit(user_id: int) -> None:
    """Raise 429 if the user sent a support message less than 60 s ago."""
    now = time.monotonic()

    # Purge expired entries to prevent unbounded memory growth
    expired_keys = [
        uid
        for uid, ts in _rate_limit_store.items()
        if now - ts >= RATE_LIMIT_SECONDS
    ]
    for uid in expired_keys:
        del _rate_limit_store[uid]

    last_sent = _rate_limit_store.get(user_id)
    if last_sent is not None and now - last_sent < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - (now - last_sent))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {remaining} seconds.",
        )
    # Record *after* validation passes so we don't block on failed attempts
    _rate_limit_store[user_id] = now


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
_PAGE_URL_RE = re.compile(r"^/[\w\-./~:@!$&'()*+,;=%?#\[\]]*$")


class SupportMessageRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Support message text",
    )
    page_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL of the page where user sent the message",
    )

    @field_validator("page_url")
    @classmethod
    def validate_page_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _PAGE_URL_RE.match(v):
            raise ValueError("page_url must be a valid relative path starting with /")
        return v


class SupportMessageResponse(BaseModel):
    success: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_telegram_text(user: User, body: SupportMessageRequest) -> str:
    safe_email = html.escape(str(user.email))
    safe_page = html.escape(body.page_url) if body.page_url else "N/A"
    safe_message = html.escape(body.message)
    return (
        "<b>📩 Support Request — FinFlow</b>\n\n"
        f"<b>From:</b> {safe_email} (ID: {user.id})\n"
        f"<b>Page:</b> {safe_page}\n\n"
        f"<b>Message:</b>\n"
        f"{safe_message}"
    )


async def _send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_SUPPORT_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/message",
    response_model=SupportMessageResponse,
    summary="Send a support message",
    description="Send a support message that is forwarded to the team via Telegram",
    responses={
        200: {"description": "Message sent successfully"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Support service temporarily unavailable"},
    },
)
async def send_support_message(
    body: SupportMessageRequest,
    user: User = Depends(get_current_user),
) -> SupportMessageResponse:
    _check_rate_limit(user.id)

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning(
            "TELEGRAM_BOT_TOKEN is not configured; support message skipped (dev mode)",
            extra={
                "category": "support",
                "operation": "send_support_message",
                "user_id": user.id,
            },
        )
        return SupportMessageResponse(success=True)

    text = _build_telegram_text(user, body)

    try:
        await _send_telegram_message(text)
    except httpx.HTTPError:
        # Log without exc_info to avoid leaking the bot token from the URL
        logger.error(
            "Failed to send support message to Telegram (HTTP error)",
            extra={
                "category": "support",
                "operation": "telegram_send_failed",
                "user_id": user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Support service is temporarily unavailable. Please try again later.",
        )
    except Exception:
        logger.error(
            "Failed to send support message to Telegram (unexpected error)",
            extra={
                "category": "support",
                "operation": "telegram_send_failed",
                "user_id": user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Support service is temporarily unavailable. Please try again later.",
        )

    logger.info(
        "Support message sent successfully",
        extra={
            "category": "support",
            "operation": "send_support_message",
            "user_id": user.id,
        },
    )
    return SupportMessageResponse(success=True)
