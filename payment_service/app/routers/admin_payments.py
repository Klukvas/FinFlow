"""Admin endpoints for payment management and outbox dead letter queue"""
from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Optional
from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.models import Payment, PaymentStatus
from ..models.outbox import OutboxEvent
from ..models.audit import AdminAuditLog
from ..schemas.payment import PaymentOut
from ..utils.admin_guard import verify_admin_token

logger = logging.getLogger("payment_service")

router = APIRouter(prefix="/admin", tags=["Admin Payments"])


def _log_admin_action(
    db: Session,
    admin_payload: dict,
    action: str,
    resource_type: str,
    request: Request,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Write an immutable audit record for an admin action."""
    entry = AdminAuditLog(
        admin_user_id=str(admin_payload.get("sub", "unknown")),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request.client else None,
    )
    db.add(entry)
    db.commit()


class AdminPaymentsListResponse:
    """Not a Pydantic model — we build the dict manually to reuse PaymentOut."""
    pass


@router.get("/payments")
def list_payments(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (PAID, FAILED, etc.)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    List all payments with pagination and filtering.
    Admin-only endpoint.
    """
    query = db.query(Payment)

    if status:
        try:
            payment_status = PaymentStatus(status)
            query = query.filter(Payment.status == payment_status)
        except ValueError:
            pass  # Invalid status — ignore filter

    if user_id:
        query = query.filter(Payment.user_id == user_id)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    offset = (page - 1) * page_size
    payments = (
        query.order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    logger.info(f"Admin {admin.get('sub')} listed payments (page={page}, total={total})")

    _log_admin_action(
        db, admin, "list_payments", "payment", request,
        details={"status_filter": status, "user_id_filter": user_id, "page": page, "total": total},
    )

    return {
        "items": [PaymentOut.model_validate(p).model_dump(mode="json") for p in payments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/payments/stats")
def get_payment_stats(
    request: Request,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    Get payment statistics: counts by status and total revenue.
    Admin-only endpoint.
    """
    rows = (
        db.query(Payment.status, func.count(Payment.id))
        .group_by(Payment.status)
        .all()
    )

    by_status = {row[0].value: row[1] for row in rows}
    total = sum(by_status.values())

    # Total revenue (sum of PAID payments)
    revenue_row = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == PaymentStatus.PAID)
        .scalar()
    )

    _log_admin_action(
        db, admin, "get_payment_stats", "payment", request,
        details={"total_payments": total},
    )

    return {
        "total": total,
        "by_status": by_status,
        "total_revenue": str(revenue_row),
    }


# ---- Dead Letter Queue (failed outbox events) ----


@router.get("/outbox/failed")
def list_failed_outbox_events(
    request: Request,
    event_type: Optional[str] = Query(None, description="Filter by event_type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    List failed outbox events (dead letter queue).
    Admin-only endpoint for investigating undelivered notifications.
    """
    query = db.query(OutboxEvent).filter(OutboxEvent.status == "failed")

    if event_type:
        query = query.filter(OutboxEvent.event_type == event_type)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    events = (
        query.order_by(OutboxEvent.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    _log_admin_action(
        db, admin, "list_failed_outbox", "outbox_event", request,
        details={"event_type_filter": event_type, "page": page, "total": total},
    )

    return {
        "items": [
            {
                "id": str(e.id),
                "aggregate_type": e.aggregate_type,
                "aggregate_id": str(e.aggregate_id),
                "event_type": e.event_type,
                "payload": e.payload,
                "destination_url": e.destination_url,
                "status": e.status,
                "retry_count": e.retry_count,
                "max_retries": e.max_retries,
                "last_error": e.last_error,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/outbox/{event_id}/replay")
def replay_outbox_event(
    event_id: str,
    request: Request,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    Reset a failed outbox event to pending for reprocessing.
    Admin-only endpoint. Only events with status='failed' can be replayed.
    """
    try:
        event_uuid = UUIDType(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID format")

    event = db.query(OutboxEvent).filter(OutboxEvent.id == event_uuid).first()

    if not event:
        raise HTTPException(status_code=404, detail="Outbox event not found")

    if event.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Only failed events can be replayed (current status: {event.status})",
        )

    admin_id = admin.get("sub", "unknown")
    original_retry_count = event.retry_count

    # Reset for reprocessing
    event.status = "pending"
    event.retry_count = 0
    event.next_retry_at = datetime.utcnow()
    event.last_error = f"Replayed by admin {admin_id} at {datetime.utcnow().isoformat()}"

    db.commit()

    _log_admin_action(
        db, admin, "replay_outbox_event", "outbox_event", request,
        resource_id=event_id,
        details={
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "original_retry_count": original_retry_count,
        },
    )

    logger.info(
        f"Admin {admin_id} replayed outbox event {event_id}",
        extra={"event_id": event_id, "admin": admin_id},
    )

    return {
        "status": "replayed",
        "event_id": event_id,
        "message": "Event reset to pending and will be processed shortly",
    }
