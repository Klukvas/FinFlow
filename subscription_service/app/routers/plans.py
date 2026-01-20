from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.plans import PlanRepository
from ..schemas.plan import PlanOut, PlanWithFeaturesOut, PlanFeatureOut
from ..models import PlanFeature, Feature


router = APIRouter()


@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    repo = PlanRepository(db)
    plans = repo.list_active()
    return [PlanOut.model_validate(p, from_attributes=True) for p in plans]


@router.get("/plans/with-features", response_model=list[PlanWithFeaturesOut])
def list_plans_with_features(db: Session = Depends(get_db)):
    """Get all active plans with their feature limits"""
    repo = PlanRepository(db)
    plans = repo.list_active()
    
    result = []
    for plan in plans:
        # Get plan features with feature details
        plan_features = (
            db.query(PlanFeature, Feature)
            .join(Feature, Feature.code == PlanFeature.feature_code)
            .filter(PlanFeature.plan_id == plan.id)
            .all()
        )
        
        # Build features dict
        features = {}
        for pf, f in plan_features:
            features[f.code] = PlanFeatureOut(
                code=f.code,
                name=f.name,
                enabled=pf.enabled,
                limit_value=pf.limit_value
            )
        
        result.append(
            PlanWithFeaturesOut(
                code=plan.code,
                name=plan.name,
                period_days=plan.period_days,
                is_active=plan.is_active,
                version=plan.version,
                features=features
            )
        )
    
    return result
