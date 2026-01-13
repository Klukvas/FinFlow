"""Admin endpoints for plan management"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Plan, Feature, PlanFeature
from ..utils.admin_guard import verify_admin_token
from ..schemas.admin import (
    PlanCreate,
    PlanUpdate,
    PlanFeaturesUpdate,
    AdminPlanOut,
    AdminPlansListResponse,
    AdminFeaturesListResponse,
    PlanFeatureOut,
    FeatureOut,
)

logger = logging.getLogger("subscription_service")

router = APIRouter(prefix="/admin", tags=["Admin Plans"])


def plan_to_admin_out(plan: Plan) -> AdminPlanOut:
    """Convert Plan model to AdminPlanOut schema"""
    return AdminPlanOut(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        period_days=plan.period_days,
        is_active=plan.is_active,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        features=[
            PlanFeatureOut(
                feature_code=pf.feature_code,
                enabled=pf.enabled,
                limit_value=pf.limit_value
            )
            for pf in plan.features
        ]
    )


@router.get("/plans", response_model=AdminPlansListResponse)
def list_all_plans(
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    List ALL plans (including inactive) for admin.
    Admin-only endpoint.
    """
    plans = db.query(Plan).order_by(Plan.code.asc()).all()
    
    logger.info(f"Admin {admin.get('sub')} listed all plans")
    
    return AdminPlansListResponse(
        items=[plan_to_admin_out(p) for p in plans]
    )


@router.get("/plans/{plan_id}", response_model=AdminPlanOut)
def get_plan(
    plan_id: int,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Get plan details by ID.
    Admin-only endpoint.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan_to_admin_out(plan)


@router.post("/plans", response_model=AdminPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Create a new plan.
    Admin-only endpoint.
    """
    # Check if plan code already exists
    existing = db.query(Plan).filter(Plan.code == data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with code '{data.code}' already exists"
        )
    
    plan = Plan(
        code=data.code,
        name=data.name,
        period_days=data.period_days,
        is_active=data.is_active
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Admin {admin.get('sub')} created plan: {plan.code}")
    
    return plan_to_admin_out(plan)


@router.patch("/plans/{plan_id}", response_model=AdminPlanOut)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Update plan details.
    Admin-only endpoint.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Update only provided fields
    if data.name is not None:
        plan.name = data.name
    if data.period_days is not None:
        plan.period_days = data.period_days
    if data.is_active is not None:
        plan.is_active = data.is_active
    
    # Increment version on update
    plan.version += 1
    
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Admin {admin.get('sub')} updated plan {plan_id}: {plan.code}")
    
    return plan_to_admin_out(plan)


@router.patch("/plans/{plan_id}/features", response_model=AdminPlanOut)
def update_plan_features(
    plan_id: int,
    data: PlanFeaturesUpdate,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Update plan feature toggles.
    Admin-only endpoint.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Validate all feature codes exist
    feature_codes = [f.feature_code for f in data.features]
    existing_features = db.query(Feature).filter(Feature.code.in_(feature_codes)).all()
    existing_codes = {f.code for f in existing_features}
    
    invalid_codes = set(feature_codes) - existing_codes
    if invalid_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature codes: {', '.join(invalid_codes)}"
        )
    
    # Delete existing plan features
    db.query(PlanFeature).filter(PlanFeature.plan_id == plan_id).delete()
    
    # Create new plan features
    for feature_data in data.features:
        plan_feature = PlanFeature(
            plan_id=plan_id,
            feature_code=feature_data.feature_code,
            enabled=feature_data.enabled,
            limit_value=feature_data.limit_value
        )
        db.add(plan_feature)
    
    # Increment plan version
    plan.version += 1
    
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Admin {admin.get('sub')} updated features for plan {plan_id}")
    
    return plan_to_admin_out(plan)


@router.get("/features", response_model=AdminFeaturesListResponse)
def list_all_features(
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    List all available features.
    Admin-only endpoint.
    """
    features = db.query(Feature).order_by(Feature.code.asc()).all()
    
    return AdminFeaturesListResponse(
        items=[FeatureOut.model_validate(f) for f in features]
    )
