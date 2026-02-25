from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..repositories.subscriptions import SubscriptionRepository
from ..repositories.plans import PlanRepository
from ..models.models import Subscription
from ..utils.errors import ValidationError, NotFoundError
from .entitlements import invalidate_entitlements_cache
from .events import EventBus
from .state_machine import validate_transition, InvalidTransitionError

logger = logging.getLogger("subscription_service.subscriptions")


class SubscriptionService:
    def __init__(self, db: Session) -> None:
        self.repo = SubscriptionRepository(db)
        self.plans = PlanRepository(db)
        self.events = EventBus()
        self.db = db

    def set_plan(self, user_id: str, plan_code: str, status: str | None = None) -> dict:
        """Set user's plan and return subscription with downgrade impact info."""
        plan = self.plans.get_by_code(plan_code)
        if plan is None or not plan.is_active:
            raise NotFoundError("Plan not found", error_code="@subscription_service/PLAN_NOT_FOUND")

        if status is not None and status not in {"active", "past_due", "canceled", "paused"}:
            raise ValidationError("Invalid status", error_code="@subscription_service/INVALID_STATUS")

        # Check for downgrade and compute impact
        downgrade_impact: list[dict] = []
        existing_sub = self.repo.get_active_subscription(user_id)
        if existing_sub and existing_sub.plan_code != plan_code:
            downgrade_impact = self._compute_downgrade_impact(
                user_id, existing_sub.plan_code, plan_code
            )

        sub = self.repo.upsert_subscription(user_id, plan_code, status)

        # Invalidate entitlements cache so new plan limits apply immediately
        invalidate_entitlements_cache(user_id)

        version, _ents = self.repo.get_entitlements(plan_code)
        self.events.publish_subscription_changed(
            user_id=user_id,
            plan_code=plan_code,
            status=sub.status,
            expires_at=sub.expires_at.isoformat() if sub.expires_at else "",
            version=version,
        )
        return {
            "subscription": sub,
            "downgrade_impact": downgrade_impact,
            "is_downgrade": len(downgrade_impact) > 0,
        }
    
    def _compute_downgrade_impact(
        self, user_id: str, old_plan_code: str, new_plan_code: str
    ) -> list[dict]:
        """Compare feature limits between old and new plan.

        Returns a list of features that are reduced, disabled, or removed.
        Also logs a warning when features are reduced.
        """
        try:
            _old_ver, old_ents = self.repo.get_entitlements(old_plan_code)
            _new_ver, new_ents = self.repo.get_entitlements(new_plan_code)
        except ValueError:
            return []  # Plan not found - nothing to compare

        reduced_features: list[dict] = []
        for feature_code, old_feat in old_ents.items():
            new_feat = new_ents.get(feature_code)
            old_limit = old_feat.get("limit_value")
            old_enabled = old_feat.get("enabled", False)

            if new_feat is None:
                # Feature removed entirely in new plan
                if old_enabled:
                    reduced_features.append(
                        {"feature": feature_code, "old_limit": old_limit, "new_limit": None, "change": "removed"}
                    )
                continue

            new_limit = new_feat.get("limit_value")
            new_enabled = new_feat.get("enabled", False)

            if old_enabled and not new_enabled:
                reduced_features.append(
                    {"feature": feature_code, "old_limit": old_limit, "new_limit": new_limit, "change": "disabled"}
                )
            elif old_limit is not None and new_limit is not None and new_limit < old_limit:
                reduced_features.append(
                    {"feature": feature_code, "old_limit": old_limit, "new_limit": new_limit, "change": "reduced"}
                )

        if reduced_features:
            logger.warning(
                f"Plan downgrade for user {user_id}: {old_plan_code} -> {new_plan_code} "
                f"reduces {len(reduced_features)} feature(s)",
                extra={
                    "user_id": user_id,
                    "old_plan": old_plan_code,
                    "new_plan": new_plan_code,
                    "reduced_features": reduced_features,
                },
            )

        return reduced_features

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
        
        # Validate transition through state machine for immediate cancellation
        if cancel_immediately:
            try:
                validate_transition(subscription.status, "canceled")
            except InvalidTransitionError:
                raise ValidationError(
                    "Subscription cannot be canceled from current state",
                    error_code="@subscription_service/INVALID_CANCELLATION",
                )
        elif subscription.status == "canceled" and not subscription.auto_renew:
            raise ValidationError(
                "Subscription is already canceled",
                error_code="@subscription_service/ALREADY_CANCELED",
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
            
            # Publish event with actual plan that was canceled
            try:
                cancel_version, _ents = self.repo.get_entitlements(subscription.plan_code)
            except ValueError:
                cancel_version = 1
            self.events.publish_subscription_changed(
                user_id=user_id,
                plan_code=subscription.plan_code,
                status="canceled",
                expires_at=subscription.expires_at.isoformat() if subscription.expires_at else "",
                version=cancel_version,
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

        # Invalidate entitlements cache so access changes take effect immediately
        invalidate_entitlements_cache(user_id)

        # TODO: Send cancellation confirmation email
        # from ..services.email import send_cancellation_email
        # send_cancellation_email(subscription)

        return subscription


