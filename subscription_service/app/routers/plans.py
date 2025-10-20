from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.plans import PlanRepository
from ..schemas.plan import PlanOut


router = APIRouter()


@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    repo = PlanRepository(db)
    plans = repo.list_active()
    return [PlanOut.model_validate(p, from_attributes=True) for p in plans]


