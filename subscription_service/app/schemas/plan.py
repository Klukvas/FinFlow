from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class FeatureRule(BaseModel):
    feature_code: str
    enabled: bool
    limit_value: Optional[int] = None


class PlanOut(BaseModel):
    code: str
    name: str
    period_days: int
    is_active: bool
    version: int

    class Config:
        from_attributes = True


