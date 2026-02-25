"""Reconciliation job: detect payment-subscription state mismatches.

Runs as a background task alongside the outbox processor.  Periodically
queries PAID subscription payments and verifies that the subscription
service actually has an active subscription for the user.  On mismatch,
re-enqueues an outbox event so the outbox processor can retry delivery.

DB operations run in a thread pool via ``asyncio.to_thread`` to avoid
blocking the event loop (SQLAlchemy sessions are synchronous).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..database import SessionLocal
from ..models.models import Payment, PaymentStatus, PaymentPurpose
from ..models.outbox import OutboxEvent
from ..config import settings

logger = logging.getLogger("payment_service.reconciliation")

BATCH_SIZE = 100


def _fetch_paid_payments() -> list[dict]:
    """Synchronous DB query — run in thread pool.

    Returns plain dicts so the ORM objects are not shared across threads.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=settings.reconciliation_lookback_hours)
        payments = (
            db.query(Payment)
            .filter(
                Payment.status == PaymentStatus.PAID,
                Payment.purpose == PaymentPurpose.SUBSCRIPTION,
                Payment.plan_code.isnot(None),
                Payment.paid_at >= cutoff,
            )
            .order_by(Payment.paid_at.desc())
            .limit(BATCH_SIZE)
            .all()
        )
        return [
            {
                "id": p.id,
                "user_id": p.user_id,
                "workspace_id": p.workspace_id,
                "plan_code": p.plan_code,
                "amount": str(p.amount),
                "currency": p.currency,
            }
            for p in payments
        ]
    finally:
        db.close()


def _handle_mismatch(payment_dict: dict, reason: str) -> bool:
    """Re-enqueue an outbox event for a mismatched payment.

    Uses INSERT ... ON CONFLICT DO NOTHING against the partial unique index
    ``uq_outbox_pending_aggregate_event`` to prevent duplicate events
    without a SELECT-then-INSERT race condition.

    Creates its own DB session for thread safety.

    Returns True if a new event was created, False if one already exists.
    """
    db = SessionLocal()
    try:
        stmt = pg_insert(OutboxEvent).values(
            id=uuid4(),
            aggregate_type="payment",
            aggregate_id=payment_dict["id"],
            event_type="payment_success",
            payload={
                "payment_id": str(payment_dict["id"]),
                "user_id": payment_dict["user_id"],
                "workspace_id": payment_dict["workspace_id"],
                "plan_code": payment_dict["plan_code"],
                "amount": payment_dict["amount"],
                "currency": payment_dict["currency"],
                "reconciliation": True,
                "mismatch_reason": reason,
            },
            destination_url=f"{settings.subscription_service_url}/v1/internal/subscriptions/activate",
            status="pending",
        ).on_conflict_do_nothing(
            index_elements=["aggregate_id", "event_type"],
            index_where=OutboxEvent.status.in_(["pending", "processing"]),
        )

        result = db.execute(stmt)
        db.commit()

        inserted = result.rowcount > 0
        if inserted:
            logger.warning(
                f"Re-enqueued outbox event for mismatched payment {payment_dict['id']}",
                extra={
                    "payment_id": str(payment_dict["id"]),
                    "user_id": payment_dict["user_id"],
                    "reason": reason,
                },
            )
        else:
            logger.info(
                f"Outbox event already pending for payment {payment_dict['id']}, skipping re-enqueue",
                extra={"payment_id": str(payment_dict["id"])},
            )

        return inserted
    finally:
        db.close()


async def _check_subscription_for_payment(
    client: httpx.AsyncClient, payment_dict: dict
) -> str | None:
    """Query subscription_service for this payment's user.

    Returns a mismatch reason string, or None if subscription is healthy.
    """
    url = f"{settings.subscription_service_url}/v1/subscriptions/{payment_dict['user_id']}"
    headers = {
        "X-Internal-Token": settings.internal_secret_token,
        "Content-Type": "application/json",
    }

    response = await client.get(url, headers=headers)

    if response.status_code == 404:
        return "no_active_subscription"

    if response.is_success:
        data = response.json()
        sub_status = data.get("status")
        sub_plan = data.get("plan_code")

        if sub_status not in ("active", "past_due", "paused"):
            return f"unexpected_status:{sub_status}"
        if sub_plan != payment_dict["plan_code"]:
            return f"plan_mismatch:expected={payment_dict['plan_code']},actual={sub_plan}"
        return None

    # 5xx or other server error — don't treat as mismatch, just skip
    return None


async def reconcile_payments() -> dict:
    """Check for PAID subscription payments without a matching active subscription.

    Returns a dict with stats: checked, mismatches, requeued, errors.
    """
    stats = {"checked": 0, "mismatches": 0, "requeued": 0, "errors": 0}

    try:
        # Run blocking DB query in a thread pool (own session, returns dicts)
        paid_payments = await asyncio.to_thread(_fetch_paid_payments)

        if not paid_payments:
            return stats

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            for payment_dict in paid_payments:
                stats["checked"] += 1
                try:
                    mismatch = await _check_subscription_for_payment(client, payment_dict)
                    if mismatch:
                        stats["mismatches"] += 1
                        # Run blocking DB write in a thread pool (own session)
                        requeued = await asyncio.to_thread(
                            _handle_mismatch, payment_dict, mismatch
                        )
                        if requeued:
                            stats["requeued"] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    logger.error(
                        f"Reconciliation check failed for payment {payment_dict['id']}: {exc}",
                        extra={"payment_id": str(payment_dict["id"])},
                    )

        if stats["mismatches"] > 0:
            logger.critical(
                f"Reconciliation found {stats['mismatches']} payment-subscription mismatches",
                extra=stats,
            )

    except Exception as exc:
        logger.error(f"Reconciliation job error: {exc}", exc_info=True)

    return stats


async def check_stale_paddle_subscriptions() -> dict:
    """Fallback for Paddle subscriptions that missed a renewal webhook.

    1. Queries subscription_service for Paddle subscriptions that expired
       recently (within grace period) but are still active/past_due.
    2. For each, polls Paddle's API for the actual subscription status.
    3. If Paddle says the subscription is active, forwards a ``paddle-event``
       with ``event_type=activated`` to trigger extension.

    Returns stats: checked, renewed, errors.
    """
    from ..clients.paddle_client import PaddleClient, PaddleClientError

    stats = {"checked": 0, "renewed": 0, "errors": 0}

    if not settings.paddle_api_key:
        return stats  # Paddle not configured — skip

    internal_headers = {
        "X-Internal-Token": settings.internal_secret_token,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            # Step 1: Get stale Paddle subscriptions from subscription_service
            url = f"{settings.subscription_service_url}/v1/internal/subscriptions:stale-paddle"
            resp = await client.get(url, headers=internal_headers)

            if not resp.is_success:
                logger.error(
                    f"Failed to fetch stale Paddle subscriptions: HTTP {resp.status_code}",
                )
                return stats

            stale_subs = resp.json()
            if not stale_subs:
                return stats

            paddle = PaddleClient()

            # Step 2: Check each against Paddle API
            for sub_info in stale_subs:
                stats["checked"] += 1
                paddle_sub_id = sub_info["paddle_subscription_id"]

                try:
                    paddle_data = await paddle.get_subscription(paddle_sub_id)
                    paddle_status = paddle_data.get("status", "")

                    if paddle_status == "active":
                        # Paddle says it's active — we missed the renewal webhook
                        # Forward an "activated" event to subscription_service
                        event_url = (
                            f"{settings.subscription_service_url}"
                            f"/v1/internal/subscriptions/paddle-event"
                        )
                        event_payload = {
                            "user_id": sub_info["user_id"],
                            "paddle_subscription_id": paddle_sub_id,
                            "event_type": "activated",
                            "reason": "reconciliation_paddle_fallback",
                        }
                        event_resp = await client.post(
                            event_url, json=event_payload, headers=internal_headers,
                        )

                        if event_resp.is_success:
                            stats["renewed"] += 1
                            logger.warning(
                                f"Paddle fallback renewed subscription for user {sub_info['user_id']}",
                                extra={
                                    "user_id": sub_info["user_id"],
                                    "paddle_subscription_id": paddle_sub_id,
                                    "subscription_id": sub_info["id"],
                                },
                            )
                        else:
                            stats["errors"] += 1
                            logger.error(
                                f"Failed to forward Paddle renewal event: HTTP {event_resp.status_code}",
                                extra={"paddle_subscription_id": paddle_sub_id},
                            )
                    else:
                        logger.info(
                            f"Paddle subscription {paddle_sub_id} status is '{paddle_status}', no action",
                        )

                except PaddleClientError as exc:
                    stats["errors"] += 1
                    logger.error(
                        f"Paddle API error checking subscription {paddle_sub_id}: {exc}",
                        extra={"paddle_subscription_id": paddle_sub_id},
                    )
                except Exception as exc:
                    stats["errors"] += 1
                    logger.error(
                        f"Unexpected error checking Paddle subscription {paddle_sub_id}: {exc}",
                        extra={"paddle_subscription_id": paddle_sub_id},
                    )

    except Exception as exc:
        logger.error(f"Paddle fallback check error: {exc}", exc_info=True)

    if stats["renewed"] > 0:
        logger.warning(
            f"Paddle fallback renewed {stats['renewed']} subscriptions",
            extra=stats,
        )

    return stats


async def run_reconciliation_loop() -> None:
    """Run the reconciliation loop indefinitely."""
    logger.info("Reconciliation job started")
    while True:
        try:
            stats = await reconcile_payments()
            if stats["checked"] > 0:
                logger.info("Reconciliation cycle completed", extra=stats)

            # Paddle renewal fallback — runs in the same loop
            paddle_stats = await check_stale_paddle_subscriptions()
            if paddle_stats["checked"] > 0:
                logger.info("Paddle fallback check completed", extra=paddle_stats)

        except Exception as exc:
            logger.error(f"Reconciliation loop error: {exc}", exc_info=True)
        await asyncio.sleep(settings.reconciliation_interval_seconds)
