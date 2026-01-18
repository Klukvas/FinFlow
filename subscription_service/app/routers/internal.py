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
        # Get plan
        plan_repo = PlanRepository(db)
        plan = plan_repo.get_by_code(notification.plan_code)
        
        if not plan:
            logger.error(f"Plan {notification.plan_code} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {notification.plan_code} not found"
            )
        
        # Create or extend subscription
        subscription_repo = SubscriptionRepository(db)
        
        from datetime import datetime, timedelta
        
        # Check if user already has subscription
        existing_subscription = subscription_repo.get_active_by_user(notification.user_id)
        
        if existing_subscription:
            # Extend existing subscription
            if existing_subscription.expires_at:
                new_expires = existing_subscription.expires_at + timedelta(days=plan.period_days)
            else:
                new_expires = datetime.utcnow() + timedelta(days=plan.period_days)
            
            existing_subscription.expires_at = new_expires
            db.commit()
            
            logger.info(
                f"Extended subscription for user {notification.user_id}",
                extra={
                    "subscription_id": existing_subscription.id,
                    "new_expires_at": new_expires.isoformat(),
                }
            )
        else:
            # Create new subscription
            from ..models.models import Subscription
            
            new_subscription = Subscription(
                user_id=notification.user_id,
                plan_code=notification.plan_code,
                status="active",
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=plan.period_days),
            )
            
            db.add(new_subscription)
            db.commit()
            
            logger.info(
                f"Created subscription for user {notification.user_id}",
                extra={
                    "subscription_id": new_subscription.id,
                    "plan_code": notification.plan_code,
                }
            )
        
        return {
            "status": "success",
            "message": "Subscription activated",
            "payment_id": notification.payment_id,
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
