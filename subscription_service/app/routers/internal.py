from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..repositories.features import FeatureRepository
from ..repositories.subscriptions import SubscriptionRepository
from ..repositories.plans import PlanRepository
from ..schemas.features import UserFeatureOut
from ..utils.auth import verify_internal_token
from ..config import settings
from ..models.models import ProcessedInternalEvent
from ..services.entitlements import invalidate_entitlements_cache


router = APIRouter()
logger = logging.getLogger("subscription_service.internal_router")


# Schemas for payment notifications
class PaymentSuccessNotification(BaseModel):
    payment_id: str
    user_id: str
    workspace_id: Optional[str] = None
    plan_code: str
    amount: str
    currency: str
    recurring_token: Optional[str] = None  # WFP legacy
    paddle_customer_id: Optional[str] = None
    paddle_subscription_id: Optional[str] = None
    paddle_price_id: Optional[str] = None


class PaymentFailureNotification(BaseModel):
    payment_id: str
    user_id: str
    plan_code: Optional[str] = None
    reason: Optional[str] = None


@router.get("/internal/features/{user_id}", response_model=list[UserFeatureOut])
def get_user_features_internal(
    user_id: str, 
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint for other services to get user's feature entitlements"""
    repo = FeatureRepository(db)
    user_features = repo.get_user_features(user_id)
    return [UserFeatureOut(**uf) for uf in user_features]


@router.post("/internal/subscriptions/activate", status_code=status.HTTP_200_OK)
async def activate_subscription_after_payment(
    notification: PaymentSuccessNotification,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Internal endpoint for payment_service to notify about successful payment
    
    Creates or extends subscription based on payment.
    """
    logger.info(
        f"Received payment success notification for user {notification.user_id}",
        extra={
            "payment_id": notification.payment_id,
            "user_id": notification.user_id,
            "plan_code": notification.plan_code,
            "amount": notification.amount,
        }
    )
    
    try:
        subscription_repo = SubscriptionRepository(db)
        plan_repo = PlanRepository(db)

        # Validate plan exists and is active
        plan = plan_repo.get_by_code(notification.plan_code)
        if not plan or not plan.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan '{notification.plan_code}' not found or inactive",
            )

        # Check existing subscription first for logging and deduplication
        existing = subscription_repo.get_active_subscription(notification.user_id)
        old_plan = existing.plan_code if existing else None

        # Deduplicate by payment_id: skip if this payment was already processed
        if existing and existing.last_payment_id == notification.payment_id:
            logger.info(
                f"Payment {notification.payment_id} already processed for user {notification.user_id}",
                extra={"payment_id": notification.payment_id, "subscription_id": existing.id},
            )
            return {
                "status": "already_processed",
                "message": "Payment already applied to subscription",
                "payment_id": notification.payment_id,
                "subscription_id": existing.id,
                "plan_code": existing.plan_code,
                "expires_at": existing.expires_at.isoformat() if existing.expires_at else None,
            }

        # Upsert subscription with commit=False for atomic update (Fix #18)
        subscription = subscription_repo.upsert_subscription(
            user_id=notification.user_id,
            plan_code=notification.plan_code,
            status="active",
            commit=False,
        )

        # Store last_payment_id for deduplication
        subscription.last_payment_id = notification.payment_id

        # Store recurring token if provided (legacy WFP flow)
        if notification.recurring_token:
            subscription.recurring_token = notification.recurring_token
            if not notification.paddle_subscription_id:
                subscription.payment_provider = "WFP"

        # Store Paddle IDs if provided (new Paddle flow)
        if notification.paddle_subscription_id:
            subscription.paddle_customer_id = notification.paddle_customer_id
            subscription.paddle_subscription_id = notification.paddle_subscription_id
            subscription.paddle_price_id = notification.paddle_price_id
            subscription.payment_provider = "PADDLE"
            subscription.auto_renew = True  # Paddle manages renewal

        # Single atomic commit for all changes (Fix #18)
        db.commit()
        db.refresh(subscription)

        # Invalidate entitlements cache so new plan limits take effect immediately
        invalidate_entitlements_cache(notification.user_id)

        if notification.paddle_subscription_id:
            logger.info(
                f"Stored Paddle IDs for subscription {subscription.id}",
                extra={
                    "subscription_id": subscription.id,
                    "paddle_subscription_id": notification.paddle_subscription_id,
                },
            )

        if old_plan:
            logger.info(
                f"Updated subscription for user {notification.user_id}",
                extra={
                    "subscription_id": subscription.id,
                    "old_plan": old_plan,
                    "new_plan": notification.plan_code,
                    "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
                }
            )
        else:
            logger.info(
                f"Created subscription for user {notification.user_id}",
                extra={
                    "subscription_id": subscription.id,
                    "plan_code": notification.plan_code,
                    "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
                }
            )
        
        return {
            "status": "success",
            "message": "Subscription activated",
            "payment_id": notification.payment_id,
            "subscription_id": subscription.id,
            "plan_code": subscription.plan_code,
            "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
        }
        
    except Exception as e:
        logger.error(
            f"Failed to activate subscription: {e}",
            extra={
                "payment_id": notification.payment_id,
                "user_id": notification.user_id,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error activating subscription"
        )


@router.post("/internal/subscriptions/payment-failed", status_code=status.HTTP_200_OK)
async def handle_payment_failure(
    notification: PaymentFailureNotification,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Internal endpoint for payment_service to notify about failed payment.

    Transitions the subscription to ``past_due`` so that the grace-period
    logic keeps access alive while retries are attempted.
    """
    from ..models.models import Subscription
    from ..services.state_machine import validate_transition, InvalidTransitionError

    logger.warning(
        f"Received payment failure notification for user {notification.user_id}",
        extra={
            "payment_id": notification.payment_id,
            "user_id": notification.user_id,
            "plan_code": notification.plan_code,
            "reason": notification.reason,
        }
    )

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == notification.user_id)
        .order_by(Subscription.id.desc())
        .first()
    )

    if not subscription:
        logger.info(
            f"No subscription found for user {notification.user_id} (payment failure)",
            extra={"payment_id": notification.payment_id},
        )
        return {
            "status": "no_subscription",
            "message": "No subscription found",
            "payment_id": notification.payment_id,
        }

    # Validate transition through state machine
    try:
        target_status = validate_transition(subscription.status, "past_due")
    except InvalidTransitionError:
        # Already past_due or canceled — no-op is fine
        logger.info(
            f"Subscription {subscription.id} already in status '{subscription.status}', "
            f"skipping past_due transition",
            extra={"subscription_id": subscription.id, "current_status": subscription.status},
        )
        return {
            "status": "no_change",
            "message": f"Subscription already {subscription.status}",
            "payment_id": notification.payment_id,
        }

    subscription.status = target_status
    db.commit()

    # Invalidate entitlements cache (grace period still provides access)
    invalidate_entitlements_cache(notification.user_id)

    logger.warning(
        f"Subscription {subscription.id} marked as past_due for user {notification.user_id}",
        extra={
            "subscription_id": subscription.id,
            "payment_id": notification.payment_id,
            "reason": notification.reason,
        },
    )

    return {
        "status": "past_due",
        "message": "Subscription marked as past_due",
        "payment_id": notification.payment_id,
        "subscription_id": subscription.id,
    }


class PaymentRefundNotification(BaseModel):
    """Notification about refunded payment"""
    payment_id: str
    user_id: str
    reason: Optional[str] = None


class PaddleSubscriptionEvent(BaseModel):
    """Notification from payment_service about Paddle subscription lifecycle events"""
    user_id: str
    paddle_subscription_id: str
    event_type: str  # "activated", "canceled", "past_due", "paused", "resumed"
    effective_from: Optional[str] = None
    reason: Optional[str] = None


@router.post("/internal/subscriptions/paddle-event", status_code=status.HTTP_200_OK)
async def handle_paddle_subscription_event(
    event: PaddleSubscriptionEvent,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Handle Paddle subscription lifecycle events with idempotency."""
    from datetime import datetime, timedelta
    from ..models.models import Subscription

    logger.info(
        f"Received Paddle subscription event: {event.event_type}",
        extra={
            "user_id": event.user_id,
            "paddle_subscription_id": event.paddle_subscription_id,
            "event_type": event.event_type,
        },
    )

    # Idempotency: prevent duplicate event processing (insert-first pattern)
    event_key = f"{event.paddle_subscription_id}:{event.event_type}"
    processed = ProcessedInternalEvent(event_key=event_key)
    try:
        db.add(processed)
        db.flush()
    except IntegrityError:
        db.rollback()
        logger.info(
            f"Duplicate Paddle event skipped: {event_key}",
            extra={"event_key": event_key},
        )
        return {"status": "duplicate", "message": "Event already processed"}

    # Find subscription by paddle_subscription_id first, then by user_id
    subscription = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == event.paddle_subscription_id
    ).first()

    if not subscription:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == event.user_id
        ).first()

    if not subscription:
        db.commit()  # Persist idempotency record to prevent infinite retries
        logger.warning(
            f"No subscription found for Paddle event",
            extra={
                "user_id": event.user_id,
                "paddle_subscription_id": event.paddle_subscription_id,
            },
        )
        return {"status": "no_subscription", "message": "No subscription found"}

    # Validate state transition before applying
    from ..services.state_machine import validate_transition, InvalidTransitionError

    try:
        target_status = validate_transition(subscription.status, event.event_type)
    except InvalidTransitionError as exc:
        db.commit()  # Persist idempotency record
        logger.warning(
            f"Rejected invalid subscription transition: {exc}",
            extra={
                "subscription_id": subscription.id,
                "current_status": subscription.status,
                "event_type": event.event_type,
            },
        )
        return {
            "status": "rejected",
            "message": str(exc),
            "current_status": subscription.status,
        }
    except ValueError as exc:
        db.commit()  # Persist idempotency record
        logger.warning(f"Unknown Paddle event type: {event.event_type}")
        return {"status": "ignored", "message": str(exc)}

    # Apply the validated transition
    previous_status = subscription.status
    subscription.status = target_status

    if event.event_type == "canceled":
        subscription.auto_renew = False
        subscription.canceled_at = datetime.utcnow()
        if event.reason:
            subscription.cancellation_reason = event.reason

    # Handle reactivation: canceled/paused → active
    if previous_status in ("canceled", "paused") and target_status == "active":
        from ..models.models import Plan
        plan = db.query(Plan).filter(Plan.code == subscription.plan_code).first()
        period_days = plan.period_days if plan else 30

        # Use Paddle's effective_from if provided, otherwise compute from now
        base_date = datetime.utcnow()
        if event.effective_from:
            try:
                base_date = datetime.fromisoformat(event.effective_from)
            except ValueError:
                pass  # Fall back to utcnow

        subscription.expires_at = base_date + timedelta(days=period_days)
        subscription.canceled_at = None
        subscription.cancellation_reason = None
        subscription.auto_renew = True

    db.commit()

    # Invalidate entitlements cache on any subscription status change
    invalidate_entitlements_cache(event.user_id)

    logger.info(
        f"Updated subscription {subscription.id} status to {subscription.status}",
        extra={
            "subscription_id": subscription.id,
            "new_status": subscription.status,
            "event_type": event.event_type,
        },
    )

    return {
        "status": "updated",
        "subscription_id": subscription.id,
        "new_status": subscription.status,
    }


class SubscriptionOut(BaseModel):
    """Subscription output for internal API"""
    id: int
    user_id: str
    plan_code: str
    status: str
    expires_at: Optional[str]
    recurring_token: Optional[str]
    payment_provider: Optional[str]
    auto_renew: bool

    # Plan details (joined)
    plan_amount: Optional[str] = None
    currency: Optional[str] = "USD"

    # Paddle Billing fields
    paddle_customer_id: Optional[str] = None
    paddle_subscription_id: Optional[str] = None


class ExtendSubscriptionRequest(BaseModel):
    """Request to extend subscription after successful renewal"""
    payment_id: str


class MarkPastDueRequest(BaseModel):
    """Request to mark subscription as past_due"""
    reason: str


@router.post("/internal/subscriptions/payment-refunded", status_code=status.HTTP_200_OK)
async def handle_payment_refund(
    notification: PaymentRefundNotification,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Internal endpoint for payment_service to notify about refunded/chargebacked payment.
    
    Cancels the subscription (user loses benefits at period end, not immediately).
    """
    logger.warning(
        f"Received payment refund notification for user {notification.user_id}",
        extra={
            "payment_id": notification.payment_id,
            "user_id": notification.user_id,
            "reason": notification.reason,
        }
    )
    
    # Cancel subscription immediately on refund - revoke access now
    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.cancel_subscription(notification.user_id, immediate=True)

    # Invalidate entitlements cache so access is revoked immediately
    invalidate_entitlements_cache(notification.user_id)

    if subscription:
        logger.info(
            f"Subscription canceled due to refund for user {notification.user_id}",
            extra={
                "payment_id": notification.payment_id,
                "user_id": notification.user_id,
                "subscription_id": subscription.id,
                "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
            }
        )
        return {
            "status": "canceled",
            "message": "Subscription canceled due to refund",
            "payment_id": notification.payment_id,
            "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
        }
    else:
        logger.info(
            f"No active subscription found for user {notification.user_id} (refund notification)",
            extra={"payment_id": notification.payment_id, "user_id": notification.user_id}
        )
        return {
            "status": "no_subscription",
            "message": "No active subscription found",
            "payment_id": notification.payment_id,
        }


@router.get("/internal/subscriptions:expiring", response_model=list[SubscriptionOut])
def get_expiring_subscriptions(
    days_ahead: int = 1,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Get subscriptions that are expiring soon and eligible for renewal
    
    Used by scheduler_service for auto-renewal.
    """
    from datetime import datetime, timedelta
    from ..models.models import Subscription, Plan
    
    # Calculate target date
    target_date = datetime.utcnow() + timedelta(days=days_ahead)
    
    # Query subscriptions expiring before target date with auto_renew enabled
    subscriptions = db.query(Subscription, Plan).join(
        Plan, Subscription.plan_code == Plan.code
    ).filter(
        Subscription.status == "active",
        Subscription.auto_renew == True,
        Subscription.expires_at <= target_date,
        Subscription.recurring_token.isnot(None),
        Subscription.payment_provider != "PADDLE",  # Paddle handles its own renewals
    ).all()
    
    logger.info(
        f"Found {len(subscriptions)} subscriptions expiring within {days_ahead} days",
        extra={"count": len(subscriptions), "days_ahead": days_ahead}
    )
    
    result = []
    for sub, plan in subscriptions:
        result.append(SubscriptionOut(
            id=sub.id,
            user_id=sub.user_id,
            plan_code=sub.plan_code,
            status=sub.status,
            expires_at=sub.expires_at.isoformat() if sub.expires_at else None,
            recurring_token=sub.recurring_token,
            payment_provider=sub.payment_provider,
            auto_renew=sub.auto_renew,
            plan_amount=str(plan.price) if plan.price is not None else "0.00",
            currency=plan.currency or "USD",
        ))
    
    return result


@router.post("/internal/subscriptions/{subscription_id}:extend", status_code=status.HTTP_200_OK)
def extend_subscription(
    subscription_id: int,
    request: ExtendSubscriptionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Extend subscription after successful renewal payment
    
    Used by scheduler_service after successful recurring payment.
    """
    from datetime import datetime, timedelta
    from ..models.models import Subscription, Plan
    
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )
    
    # Get plan to determine billing period
    plan = db.query(Plan).filter(Plan.code == subscription.plan_code).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {subscription.plan_code} not found"
        )
    
    # Extend expires_at by plan period (guard against NULL expires_at)
    base_date = subscription.expires_at or datetime.utcnow()
    new_expires_at = base_date + timedelta(days=plan.period_days)
    subscription.expires_at = new_expires_at
    subscription.next_billing_date = new_expires_at
    subscription.last_payment_id = request.payment_id
    subscription.status = "active"  # Ensure status is active
    
    db.commit()
    db.refresh(subscription)
    
    logger.info(
        f"Extended subscription {subscription_id} to {new_expires_at}",
        extra={
            "subscription_id": subscription_id,
            "user_id": subscription.user_id,
            "payment_id": request.payment_id,
            "new_expires_at": new_expires_at.isoformat(),
        }
    )
    
    return {
        "status": "extended",
        "subscription_id": subscription.id,
        "expires_at": new_expires_at.isoformat(),
        "payment_id": request.payment_id,
    }


@router.post("/internal/subscriptions/{subscription_id}:mark_past_due", status_code=status.HTTP_200_OK)
def mark_subscription_past_due(
    subscription_id: int,
    request: MarkPastDueRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Mark subscription as past_due after failed renewal

    Used by scheduler_service when recurring payment fails.
    """
    from ..models.models import Subscription
    from ..services.state_machine import validate_transition, InvalidTransitionError

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )

    try:
        target_status = validate_transition(subscription.status, "past_due")
    except InvalidTransitionError:
        # Already past_due or canceled — no-op
        return {
            "status": subscription.status,
            "subscription_id": subscription.id,
            "reason": request.reason,
            "message": f"No transition needed, already {subscription.status}",
        }

    subscription.status = target_status

    db.commit()
    db.refresh(subscription)
    
    logger.warning(
        f"Marked subscription {subscription_id} as past_due",
        extra={
            "subscription_id": subscription_id,
            "user_id": subscription.user_id,
            "reason": request.reason,
        }
    )
    
    return {
        "status": "past_due",
        "subscription_id": subscription.id,
        "reason": request.reason,
    }


@router.get("/internal/subscriptions:stale-paddle")
def get_stale_paddle_subscriptions(
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
):
    """
    Return Paddle-managed subscriptions that expired recently but are still
    marked as active.  These may have missed a renewal webhook and need to
    be verified against the Paddle API.

    Used by payment_service's reconciliation loop as a fallback.
    """
    from datetime import datetime, timedelta
    from ..models.models import Subscription

    now = datetime.utcnow()
    grace_deadline = now - timedelta(days=settings.grace_period_days)

    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.payment_provider == "PADDLE",
            Subscription.paddle_subscription_id.isnot(None),
            Subscription.status.in_(["active", "past_due"]),
            Subscription.auto_renew == True,
            # Expired but within grace period (missed webhook window)
            Subscription.expires_at <= now,
            Subscription.expires_at > grace_deadline,
        )
        .all()
    )

    logger.info(
        f"Found {len(subscriptions)} stale Paddle subscriptions",
        extra={"count": len(subscriptions)},
    )

    return [
        {
            "id": sub.id,
            "user_id": sub.user_id,
            "plan_code": sub.plan_code,
            "paddle_subscription_id": sub.paddle_subscription_id,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            "status": sub.status,
        }
        for sub in subscriptions
    ]
