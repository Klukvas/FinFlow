"""
Cancellation schemas for API requests and responses
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""
    cancellation_reason: str | None = Field(
        None,
        description="Reason for cancellation",
        max_length=32,
        examples=["too_expensive", "not_using", "missing_features", "other"]
    )
    cancellation_comment: str | None = Field(
        None,
        description="Optional comment explaining cancellation",
        max_length=500
    )
    cancel_immediately: bool = Field(
        False,
        description="Cancel immediately (lose access now) vs cancel at period end (keep access)"
    )


class CancelSubscriptionResponse(BaseModel):
    """Response after canceling subscription"""
    id: int
    user_id: str
    plan_code: str
    status: str
    auto_renew: bool
    canceled_at: datetime | None
    expires_at: datetime | None
    cancellation_reason: str | None
    access_ends_at: datetime | None  # When user will lose access
    message: str  # User-friendly message
    
    class Config:
        from_attributes = True
