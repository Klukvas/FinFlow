from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from ..repositories.subscriptions import SubscriptionRepository
from ..repositories.plans import PlanRepository
from ..utils.errors import ValidationError, NotFoundError
from .events import EventBus


class SubscriptionService:
    def __init__(self, db: Session) -> None:
        self.repo = SubscriptionRepository(db)
        self.plans = PlanRepository(db)
        self.events = EventBus()

    def set_plan(self, user_id: str, plan_code: str, status: str | None = None):
        plan = self.plans.get_by_code(plan_code)
        if plan is None or not plan.is_active:
            raise NotFoundError("Plan not found", error_code="@subscription_service/PLAN_NOT_FOUND")

        if status is not None and status not in {"active", "past_due", "canceled", "paused"}:
            raise ValidationError("Invalid status", error_code="@subscription_service/INVALID_STATUS")

        sub = self.repo.upsert_subscription(user_id, plan_code, status)

        version, _ents = self.repo.get_entitlements(plan_code)
        self.events.publish_subscription_changed(
            user_id=user_id,
            plan_code=plan_code,
            status=sub.status,
            expires_at=sub.expires_at.isoformat() if sub.expires_at else "",
            version=version,
        )
        from app.main import subs_changes
        subs_changes.inc()
        return sub


