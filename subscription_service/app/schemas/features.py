from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class FeatureOut(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PlanFeatureOut(BaseModel):
    feature_code: str
    enabled: bool
    limit_value: Optional[int] = None

    class Config:
        from_attributes = True


class UserFeatureOut(BaseModel):
    feature_code: str
    enabled: bool
    limit_value: Optional[int] = None
    plan_code: str

    class Config:
        from_attributes = True
