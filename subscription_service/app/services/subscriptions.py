from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..repositories.subscriptions import SubscriptionRepository
from ..repositories.plans import PlanRepository
from ..models.models import Subscription
from ..utils.errors import ValidationError, NotFoundError
from .events import EventBus

logger = logging.getLogger("subscription_service.subscriptions")


class SubscriptionService:
    def __init__(self, db: Session) -> None:
        self.repo = SubscriptionRepository(db)
        self.plans = PlanRepository(db)
        self.events = EventBus()
        self.db = db

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
        return sub
    
    def cancel_subscription(
        self,
        user_id: str,
        cancellation_reason: str | None,
        cancellation_comment: str | None,
        cancel_immediately: bool,
        ip_address: str,
    ) -> Subscription:
        """
        Cancel user's subscription.
        
        Sets auto_renew=false to prevent future charges.
        Optionally cancels immediately (lose access now) or at period end (keep access).
        
        Args:
            user_id: User ID
            cancellation_reason: Reason for cancellation
            cancellation_comment: Optional comment
            cancel_immediately: If True, cancel now. If False, cancel at period end
            ip_address: User's IP address for audit trail
            
        Returns:
            Updated subscription
            
        Raises:
            NotFoundError: If no active subscription found
            ValidationError: If subscription already canceled
        """
        # Get user's subscription
        subscription = self.db.query(Subscription).filter_by(user_id=user_id).first()
        
        if not subscription:
            raise NotFoundError(
                "No subscription found for this user",
                error_code="@subscription_service/NO_SUBSCRIPTION"
            )
        
        # Check if already canceled
        if subscription.status == "canceled" and not subscription.auto_renew:
            raise ValidationError(
                "Subscription is already canceled",
                error_code="@subscription_service/ALREADY_CANCELED"
            )
        
        # CRITICAL: Set auto_renew=false to prevent future charges
        subscription.auto_renew = False
        subscription.canceled_at = datetime.utcnow()
        subscription.cancellation_reason = cancellation_reason
        subscription.cancellation_comment = cancellation_comment
        subscription.cancellation_ip_address = ip_address
        
        # Handle immediate vs period-end cancellation
        if cancel_immediately:
            # Immediate cancellation: revoke access now
            subscription.status = "canceled"
            subscription.expires_at = datetime.utcnow()
            
            # Publish event to revoke features immediately
            self.events.publish_subscription_changed(
                user_id=user_id,
                plan_code="basic",  # Downgrade to free plan
                status="canceled",
                expires_at="",
                version=1,
            )
            
            logger.info(
                f"Subscription {subscription.id} canceled immediately for user {user_id}",
                extra={
                    "subscription_id": subscription.id,
                    "user_id": user_id,
                    "reason": cancellation_reason,
                    "immediate": True
                }
            )
        else:
            # Period-end cancellation: keep access until expires_at
            # Status remains "active", but auto_renew=false prevents renewal
            logger.info(
                f"Subscription {subscription.id} canceled at period end for user {user_id}",
                extra={
                    "subscription_id": subscription.id,
                    "user_id": user_id,
                    "reason": cancellation_reason,
                    "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
                    "immediate": False
                }
            )
        
        self.db.commit()
        self.db.refresh(subscription)
        
        # TODO: Send cancellation confirmation email
        # from ..services.email import send_cancellation_email
        # send_cancellation_email(subscription)
        
        return subscription


