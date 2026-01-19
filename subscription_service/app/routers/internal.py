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
