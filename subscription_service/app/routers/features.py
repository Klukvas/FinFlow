from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.features import FeatureRepository
from ..schemas.features import FeatureOut, PlanFeatureOut, UserFeatureOut


router = APIRouter()


@router.get("/features", response_model=list[FeatureOut])
def list_features(db: Session = Depends(get_db)):
    """List all available features"""
    repo = FeatureRepository(db)
    features = repo.list_all()
    return [FeatureOut.model_validate(f, from_attributes=True) for f in features]


@router.get("/plans/{plan_code}/features", response_model=list[PlanFeatureOut])
def get_plan_features(plan_code: str, db: Session = Depends(get_db)):
    """Get features and restrictions for a specific plan"""
    repo = FeatureRepository(db)
    plan_features = repo.get_plan_features(plan_code)
    return [PlanFeatureOut.model_validate(pf, from_attributes=True) for pf in plan_features]


@router.get("/features/{user_id}", response_model=list[UserFeatureOut])
def get_user_features(user_id: str, db: Session = Depends(get_db)):
    """Get user's feature entitlements with plan context"""
    repo = FeatureRepository(db)
    user_features = repo.get_user_features(user_id)
    return [UserFeatureOut(**uf) for uf in user_features]
