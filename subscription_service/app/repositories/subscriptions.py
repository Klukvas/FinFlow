from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from ..models import Subscription, Plan, PlanFeature, Feature


class SubscriptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_subscription(self, user_id: str, plan_code: str, status: Optional[str] = None) -> Subscription:
        sub = self.db.query(Subscription).filter(Subscription.user_id == user_id).first()
        plan = self.db.query(Plan).filter(Plan.code == plan_code).first()
        if plan is None:
            raise ValueError("PLAN_NOT_FOUND")

        now = datetime.utcnow()
        expires_at = now + timedelta(days=plan.period_days)

        if sub is None:
            sub = Subscription(
                user_id=user_id,
                plan_code=plan_code,
                status=status or "active",
                started_at=now,
                expires_at=expires_at,
            )
            self.db.add(sub)
        else:
            sub.plan_code = plan_code
            sub.status = status or "active"
            sub.started_at = now
            sub.expires_at = expires_at
            sub.canceled_at = None

        self.db.commit()
        self.db.refresh(sub)
        return sub

    def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .filter(Subscription.status.in_(["active", "past_due", "paused"]))
            .first()
        )

    def get_entitlements(self, plan_code: str) -> tuple[int, dict[str, dict[str, Optional[int]]]]:
        plan: Plan | None = self.db.query(Plan).filter(Plan.code == plan_code).first()
        if plan is None:
            raise ValueError("PLAN_NOT_FOUND")
        q = (
            self.db.query(PlanFeature)
            .join(Feature, Feature.code == PlanFeature.feature_code)
            .filter(PlanFeature.plan_id == plan.id)
        )
        ents: dict[str, dict[str, Optional[int]]] = {}
        for pf in q.all():
            ents[pf.feature_code] = {"enabled": pf.enabled, "limit_value": pf.limit_value}
        return plan.version, ents


