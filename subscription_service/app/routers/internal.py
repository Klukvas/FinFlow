from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.features import FeatureRepository
from ..repositories.subscriptions import SubscriptionRepository
from ..repositories.plans import PlanRepository
from ..schemas.features import UserFeatureOut
from ..utils.errors import AuthError


router = APIRouter()
logger = logging.getLogger("subscription_service.internal_router")


from ..config import settings


def verify_internal_token(internal_token: str = Header(alias="X-Internal-Token")) -> None:
    """Verify internal service token"""
    if internal_token != settings.internal_secret_token:
        raise AuthError("Invalid internal token", error_code="@subscription_service/INVALID_INTERNAL_TOKEN")


# Schemas for payment notifications
class PaymentSuccessNotification(BaseModel):
    payment_id: str
    user_id: str
    workspace_id: Optional[str] = None
    plan_code: str
    amount: str
    currency: str
    recurring_token: Optional[str] = None  # Token for auto-renewal


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
        # Use upsert_subscription which handles create/update properly
        subscription_repo = SubscriptionRepository(db)
        
        # Check existing subscription first for logging
        existing = subscription_repo.get_active_subscription(notification.user_id)
        old_plan = existing.plan_code if existing else None
        
        # Upsert subscription (creates new or updates existing)
        subscription = subscription_repo.upsert_subscription(
            user_id=notification.user_id,
            plan_code=notification.plan_code,
            status="active"
        )
        
        # Store recurring token if provided
        if notification.recurring_token:
            subscription.recurring_token = notification.recurring_token
            subscription.payment_provider = "WAYFORPAY"
            subscription.last_payment_id = notification.payment_id
            db.commit()
            logger.info(
                f"Stored recurring token for subscription {subscription.id}",
                extra={
                    "subscription_id": subscription.id,
                    "has_token": True,
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
            detail=f"Failed to activate subscription: {str(e)}"
        )


@router.post("/internal/subscriptions/payment-failed", status_code=status.HTTP_200_OK)
async def handle_payment_failure(
    notification: PaymentFailureNotification,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """
    Internal endpoint for payment_service to notify about failed payment
    
    Logs the failure for audit purposes.
    """
    logger.warning(
        f"Received payment failure notification for user {notification.user_id}",
        extra={
            "payment_id": notification.payment_id,
            "user_id": notification.user_id,
            "plan_code": notification.plan_code,
            "reason": notification.reason,
        }
    )
    
    # In a real implementation, you might:
    # - Send notification to user about failed payment
    # - Update subscription status to past_due
    # - Create audit log entry
    # - Trigger retry logic
    
    return {
        "status": "acknowledged",
        "message": "Payment failure recorded",
        "payment_id": notification.payment_id,
    }


class PaymentRefundNotification(BaseModel):
    """Notification about refunded payment"""
    payment_id: str
    user_id: str
    reason: Optional[str] = None


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
    currency: Optional[str] = "UAH"


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
    
    # Cancel subscription - user keeps benefits until expires_at
    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.cancel_subscription(notification.user_id)
    
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
    ).all()
    
    logger.info(
        f"Found {len(subscriptions)} subscriptions expiring within {days_ahead} days",
        extra={"count": len(subscriptions), "days_ahead": days_ahead}
    )
    
    result = []
    for sub, plan in subscriptions:
        # Calculate plan amount (would come from a pricing table in production)
        # For now, use a simple mapping
        plan_amounts = {
            "pro-monthly": "299.00",
            "basic-monthly": "99.00",
            "free": "0.00",
        }
        
        result.append(SubscriptionOut(
            id=sub.id,
            user_id=sub.user_id,
            plan_code=sub.plan_code,
            status=sub.status,
            expires_at=sub.expires_at.isoformat() if sub.expires_at else None,
            recurring_token=sub.recurring_token,
            payment_provider=sub.payment_provider,
            auto_renew=sub.auto_renew,
            plan_amount=plan_amounts.get(sub.plan_code, "0.00"),
            currency="UAH",
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
    
    # Extend expires_at by plan period
    new_expires_at = subscription.expires_at + timedelta(days=plan.period_days)
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
    
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )
    
    subscription.status = "past_due"
    
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
