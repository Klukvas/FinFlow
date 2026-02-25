from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from ..models import Subscription, Plan, PlanFeature, Feature


class SubscriptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_subscription(self, user_id: str, plan_code: str, status: Optional[str] = None, commit: bool = True) -> Subscription:
        """
        Create or update subscription.
        
        Upgrade/Downgrade/Renewal logic:
        - Same plan renewal: extend from current expires_at (don't lose remaining days)
        - Different plan (upgrade/downgrade): start new period from NOW
        - New subscription: start from NOW
        """
        # Order by id DESC to get the most recent subscription if multiple exist
        sub = self.db.query(Subscription).filter(Subscription.user_id == user_id).order_by(Subscription.id.desc()).first()
        plan = self.db.query(Plan).filter(Plan.code == plan_code).first()
        if plan is None:
            raise ValueError("PLAN_NOT_FOUND")

        now = datetime.utcnow()

        if sub is None:
            # New subscription - start from now
            sub = Subscription(
                user_id=user_id,
                plan_code=plan_code,
                status=status or "active",
                started_at=now,
                expires_at=now + timedelta(days=plan.period_days),
            )
            self.db.add(sub)
        else:
            # Existing subscription
            is_same_plan = sub.plan_code == plan_code
            has_time_remaining = sub.expires_at and sub.expires_at > now
            
            if is_same_plan and has_time_remaining:
                # Same plan renewal - extend from current expires_at
                # User keeps their remaining days
                sub.expires_at = sub.expires_at + timedelta(days=plan.period_days)
            else:
                # Different plan (upgrade/downgrade) OR expired - start fresh from now
                sub.started_at = now
                sub.expires_at = now + timedelta(days=plan.period_days)
            
            sub.plan_code = plan_code
            sub.status = status or "active"
            sub.canceled_at = None

        if commit:
            self.db.commit()
            self.db.refresh(sub)
        else:
            self.db.flush()
        return sub

    def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """
        Get subscription that should provide benefits.

        Returns subscription if:
        - Status is active/past_due/paused AND not expired (with grace period), OR
        - Status is canceled but expires_at is still in the future
          (user keeps benefits until end of billing period, NO grace period)

        The grace period allows non-canceled subscriptions a buffer after
        expires_at so that failed renewal payments don't immediately revoke
        access.
        """
        from sqlalchemy import or_, and_
        from ..config import settings

        now = datetime.utcnow()
        grace_deadline = now - timedelta(days=settings.grace_period_days)

        return (
            self.db.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .filter(
                or_(
                    # Active statuses - allow grace period after expires_at
                    and_(
                        Subscription.status.in_(["active", "past_due", "paused"]),
                        or_(
                            Subscription.expires_at > now,            # Not expired yet
                            Subscription.expires_at.is_(None),        # No expiry (unlimited)
                            Subscription.expires_at > grace_deadline  # Within grace period
                        )
                    ),
                    # Canceled but not yet expired - strict, NO grace period
                    and_(
                        Subscription.status == "canceled",
                        Subscription.expires_at > now
                    )
                )
            )
            .first()
        )

    def get_subscription_by_user(self, user_id: str) -> Optional[Subscription]:
        """Get subscription by user ID (any status)"""
        # Order by id DESC to get the most recent subscription if multiple exist
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).order_by(Subscription.id.desc()).first()

    def cancel_subscription(self, user_id: str, immediate: bool = False) -> Optional[Subscription]:
        """
        Cancel subscription.

        Args:
            user_id: The user whose subscription to cancel.
            immediate: If True, set expires_at to now (revoke access immediately).
                       Used for refund-triggered cancellations.
                       If False, user keeps benefits until original expires_at.
        """
        sub = self.get_subscription_by_user(user_id)
        if sub is None:
            return None

        sub.status = "canceled"
        sub.auto_renew = False
        sub.canceled_at = datetime.utcnow()

        if immediate:
            sub.expires_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(sub)
        return sub

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


