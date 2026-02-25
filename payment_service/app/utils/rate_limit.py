"""Redis-based rate limiting for payment endpoints."""
from __future__ import annotations

import logging
from typing import Optional

import redis
from fastapi import Depends, Header, HTTPException, status

from ..config import settings
from ..utils.jwt import get_current_user, JWTPayload

logger = logging.getLogger("payment_service.rate_limit")

# Defaults
_MAX_PAYMENT_REQUESTS = 5
_WINDOW_SECONDS = 60

_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def check_rate_limit(
    redis_client: redis.Redis,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> bool:
    """Return True if the request is within rate limits, False if exceeded.

    Uses a simple Redis INCR + EXPIRE sliding-window counter.
    """
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    return current <= max_requests


async def require_payment_rate_limit(
    current_user: JWTPayload = Depends(get_current_user),
) -> None:
    """FastAPI dependency that enforces per-user rate limit on payment creation."""
    r = _get_redis()
    key = f"rate:payment:{current_user.user_id}"

    if not check_rate_limit(r, key, _MAX_PAYMENT_REQUESTS, _WINDOW_SECONDS):
        logger.warning(
            "Payment rate limit exceeded",
            extra={"user_id": str(current_user.user_id), "key": key},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many payment requests. Please wait before trying again.",
        )
