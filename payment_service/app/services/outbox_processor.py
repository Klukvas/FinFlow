"""Background processor for outbox events.

Polls the outbox_events table for pending events and delivers them
via HTTP POST with exponential backoff retry.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.outbox import OutboxEvent
from ..config import settings

logger = logging.getLogger("payment_service.outbox_processor")

POLL_INTERVAL_SECONDS = 10
BATCH_SIZE = 50
BASE_BACKOFF_SECONDS = 30


async def process_outbox_events() -> int:
    """Process a batch of pending outbox events.

    Returns the number of events successfully delivered.
    """
    db: Session = SessionLocal()
    delivered_count = 0

    try:
        now = datetime.utcnow()
        events = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status.in_(["pending", "processing"]),
                OutboxEvent.next_retry_at <= now,
            )
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
            .all()
        )

        if not events:
            return 0

        logger.info(f"Processing {len(events)} outbox events")

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            for event in events:
                event.status = "processing"
                db.commit()

                try:
                    headers = {
                        "Content-Type": "application/json",
                        "X-Internal-Token": settings.internal_secret_token,
                    }
                    if event.headers:
                        headers.update(event.headers)

                    response = await client.post(
                        event.destination_url,
                        json=event.payload,
                        headers=headers,
                    )

                    if response.is_success:
                        event.status = "delivered"
                        event.delivered_at = datetime.utcnow()
                        delivered_count += 1
                        logger.info(
                            f"Outbox event {event.id} delivered successfully",
                            extra={
                                "event_id": str(event.id),
                                "event_type": event.event_type,
                                "destination": event.destination_url,
                            },
                        )
                    elif response.status_code < 500:
                        # Client error (4xx) - don't retry, mark as failed
                        event.status = "failed"
                        event.last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                        logger.error(
                            f"Outbox event {event.id} failed with client error",
                            extra={
                                "event_id": str(event.id),
                                "status_code": response.status_code,
                                "error": event.last_error,
                            },
                        )
                    else:
                        # Server error (5xx) - retry
                        _schedule_retry(event, f"HTTP {response.status_code}")

                except (httpx.ConnectError, httpx.TimeoutException) as exc:
                    _schedule_retry(event, str(exc))

                except Exception as exc:
                    _schedule_retry(event, str(exc))
                    logger.error(
                        f"Unexpected error delivering outbox event {event.id}: {exc}",
                        exc_info=True,
                    )

                db.commit()

    except Exception as exc:
        logger.error(f"Outbox processor error: {exc}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    return delivered_count


def _schedule_retry(event: OutboxEvent, error: str) -> None:
    """Schedule the next retry with exponential backoff."""
    event.retry_count += 1
    event.last_error = error[:1000]

    if event.retry_count >= event.max_retries:
        event.status = "failed"
        logger.critical(
            f"Outbox event {event.id} exhausted all retries",
            extra={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "aggregate_id": str(event.aggregate_id),
                "retry_count": event.retry_count,
            },
        )
    else:
        event.status = "pending"
        backoff = BASE_BACKOFF_SECONDS * (2 ** (event.retry_count - 1))
        event.next_retry_at = datetime.utcnow() + timedelta(seconds=min(backoff, 3600))
        logger.warning(
            f"Outbox event {event.id} retry {event.retry_count}/{event.max_retries} "
            f"scheduled at {event.next_retry_at}",
            extra={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "error": error[:200],
            },
        )


async def run_outbox_processor() -> None:
    """Run the outbox processor loop indefinitely."""
    logger.info("Outbox processor started")
    while True:
        try:
            await process_outbox_events()
        except Exception as exc:
            logger.error(f"Outbox processor loop error: {exc}", exc_info=True)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
