"""Public pricing endpoint — returns plan prices fetched from Paddle.

Cached in-memory for 1 hour so we don't hit Paddle on every page load.
Falls back to configured amounts (with shorter 5-min TTL) when Paddle is
unreachable.  No auth required — pricing is public information.
"""
from __future__ import annotations

import asyncio
import logging
import time
from decimal import Decimal
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..clients.paddle_client import PaddleClient, PaddleClientError
from ..config import settings, PaddlePriceEntry

logger = logging.getLogger("payment_service.pricing")

router = APIRouter(tags=["pricing"])

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_paddle_client = PaddleClient()

_CACHE_TTL_NORMAL = 3600   # 1 hour  — at least one live price succeeded
_CACHE_TTL_FALLBACK = 300  # 5 min   — every price came from fallback

_cached_pricing: list[PlanPrice] | None = None  # type: ignore[name-defined]  # forward ref
_cache_expires_at: float = 0.0
_cache_lock = asyncio.Lock()

_TWO_PLACES = Decimal("0.01")


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------
class PlanPrice(BaseModel):
    plan_code: str
    price: str  # e.g. "9.99" — string to avoid float rounding
    currency: str  # e.g. "USD"
    billing_period: str  # e.g. "month"
    paddle_price_id: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fallback_plan_price(entry: PaddlePriceEntry) -> PlanPrice:
    """Build a PlanPrice from the local config entry."""
    return PlanPrice(
        plan_code=entry.plan_code,
        price=str(entry.amount),
        currency=entry.currency,
        billing_period=entry.billing_period,
        paddle_price_id=entry.paddle_price_id,
    )


async def _fetch_single_price(entry: PaddlePriceEntry) -> tuple[PlanPrice, bool]:
    """Fetch one price from Paddle; return (PlanPrice, is_fallback).

    Returns the live price on success, or the config fallback on failure.
    """
    try:
        data = await _paddle_client.get_price(entry.paddle_price_id)
        unit_price = data.get("unit_price", {})
        raw_amount = unit_price.get("amount", "0")
        amount = (Decimal(raw_amount) / 100).quantize(_TWO_PLACES)
        currency = unit_price.get("currency_code", entry.currency).upper()
        billing_cycle = data.get("billing_cycle", {})
        period = billing_cycle.get("interval", entry.billing_period)

        return PlanPrice(
            plan_code=entry.plan_code,
            price=str(amount),
            currency=currency,
            billing_period=period,
            paddle_price_id=entry.paddle_price_id,
        ), False
    except PaddleClientError as exc:
        logger.warning(
            "Failed to fetch price from Paddle, using config fallback",
            extra={"price_id": entry.paddle_price_id, "error": str(exc)},
        )
        return _fallback_plan_price(entry), True


async def _refresh_pricing(
    price_entries: list[PaddlePriceEntry],
) -> tuple[list[PlanPrice], float]:
    """Fetch all prices concurrently; return (results, ttl)."""
    fetched = await asyncio.gather(
        *(_fetch_single_price(entry) for entry in price_entries)
    )

    results = [plan_price for plan_price, _ in fetched]
    all_fallback = all(is_fallback for _, is_fallback in fetched)
    ttl = _CACHE_TTL_FALLBACK if all_fallback else _CACHE_TTL_NORMAL

    return results, ttl


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.get("/pricing", response_model=list[PlanPrice])
async def get_plan_pricing() -> list[PlanPrice]:
    """Return current plan pricing from Paddle (cached).

    Falls back to the configured PADDLE_PRICE_MAP amounts if
    Paddle API is unreachable (cached for 5 min instead of 1 hour).
    """
    global _cached_pricing, _cache_expires_at  # noqa: PLW0603

    # Fast path — cache hit (no lock needed for reads of immutable list)
    if _cached_pricing is not None and time.monotonic() < _cache_expires_at:
        return _cached_pricing

    async with _cache_lock:
        # Double-check after acquiring lock
        if _cached_pricing is not None and time.monotonic() < _cache_expires_at:
            return _cached_pricing

        price_entries = list(settings._price_map_by_plan.values())

        if not price_entries:
            # No paid plans configured — return empty list (basic is free)
            return []

        results, ttl = await _refresh_pricing(price_entries)

        _cached_pricing = results
        _cache_expires_at = time.monotonic() + ttl

        logger.info(
            "Plan pricing refreshed",
            extra={"plans": len(results), "ttl_seconds": ttl},
        )

    return results
