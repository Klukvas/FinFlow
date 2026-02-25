"""Admin-specific schemas for subscription service"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class PlanFeatureIn(BaseModel):
    """Feature toggle for a plan"""
    feature_code: str
    enabled: bool = True
    limit_value: Optional[int] = None


class PlanCreate(BaseModel):
    """Schema for creating a new plan"""
    code: str = Field(..., min_length=1, max_length=64, pattern="^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1, max_length=255)
    period_days: int = Field(..., ge=1)
    is_active: bool = True


class PlanUpdate(BaseModel):
    """Schema for updating a plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    period_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class PlanFeaturesUpdate(BaseModel):
    """Schema for updating plan features"""
    features: List[PlanFeatureIn]


class PlanFeatureOut(BaseModel):
    """Feature details in plan response"""
    feature_code: str
    enabled: bool
    limit_value: Optional[int] = None

    class Config:
        from_attributes = True


class AdminPlanOut(BaseModel):
    """Full plan details for admin view"""
    id: int
    code: str
    name: str
    period_days: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    features: List[PlanFeatureOut] = []

    class Config:
        from_attributes = True


class AdminPlansListResponse(BaseModel):
    """List of plans for admin"""
    items: List[AdminPlanOut]


class FeatureOut(BaseModel):
    """Feature details"""
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AdminFeaturesListResponse(BaseModel):
    """List of features for admin"""
    items: List[FeatureOut]


# --- Admin Subscription schemas ---

class AdminSubscriptionOut(BaseModel):
    """Full subscription details for admin view"""
    id: int
    user_id: str
    plan_code: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    auto_renew: bool = True
    payment_provider: Optional[str] = None
    last_payment_id: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    paddle_customer_id: Optional[str] = None
    paddle_subscription_id: Optional[str] = None
    paddle_price_id: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancellation_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminSubscriptionsListResponse(BaseModel):
    """Paginated list of subscriptions for admin"""
    items: List[AdminSubscriptionOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubscriptionStatsOut(BaseModel):
    """Subscription status counts"""
    total: int
    active: int
    past_due: int
    canceled: int
    paused: int
