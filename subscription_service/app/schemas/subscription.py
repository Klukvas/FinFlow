from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class SetPlanIn(BaseModel):
    plan_code: str
    status: Optional[str] = None  # optional override


class SubscriptionOut(BaseModel):
    user_id: str
    plan_code: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    auto_renew: bool = True  # CRITICAL: Required for frontend to determine if subscription is canceled
    recurring_token: Optional[str] = None
    next_billing_date: Optional[datetime] = None

    class Config:
        from_attributes = True


