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
