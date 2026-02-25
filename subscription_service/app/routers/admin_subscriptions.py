"""Admin endpoints for subscription management"""
from __future__ import annotations

import logging
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Subscription
from ..utils.admin_guard import verify_admin_token
from ..schemas.admin import (
    AdminSubscriptionOut,
    AdminSubscriptionsListResponse,
    SubscriptionStatsOut,
)

logger = logging.getLogger("subscription_service")

router = APIRouter(prefix="/admin", tags=["Admin Subscriptions"])


@router.get("/subscriptions", response_model=AdminSubscriptionsListResponse)
def list_subscriptions(
    status: Optional[str] = Query(None, description="Filter by status"),
    plan_code: Optional[str] = Query(None, description="Filter by plan code"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    List all subscriptions with pagination and filtering.
    Admin-only endpoint.
    """
    query = db.query(Subscription)

    if status:
        query = query.filter(Subscription.status == status)
    if plan_code:
        query = query.filter(Subscription.plan_code == plan_code)
    if user_id:
        query = query.filter(Subscription.user_id == user_id)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    offset = (page - 1) * page_size
    subscriptions = (
        query.order_by(Subscription.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    logger.info(f"Admin {admin.get('sub')} listed subscriptions (page={page}, total={total})")

    return AdminSubscriptionsListResponse(
        items=[AdminSubscriptionOut.model_validate(s) for s in subscriptions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/subscriptions/stats", response_model=SubscriptionStatsOut)
def get_subscription_stats(
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """
    Get subscription status counts.
    Admin-only endpoint.
    """
    rows = (
        db.query(Subscription.status, func.count(Subscription.id))
        .group_by(Subscription.status)
        .all()
    )

    counts = {row[0]: row[1] for row in rows}
    total = sum(counts.values())

    return SubscriptionStatsOut(
        total=total,
        active=counts.get("active", 0),
        past_due=counts.get("past_due", 0),
        canceled=counts.get("canceled", 0),
        paused=counts.get("paused", 0),
    )
