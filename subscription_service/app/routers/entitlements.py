from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.subscriptions import SubscriptionRepository
from ..services.entitlements import EntitlementsService
from ..schemas.entitlements import EntitlementsOut
from app.main import p95_entitlements


router = APIRouter()


@router.get("/entitlements/{user_id}", response_model=EntitlementsOut)
def get_entitlements(user_id: str, db: Session = Depends(get_db)):
    with p95_entitlements.time():
        repo = SubscriptionRepository(db)
        service = EntitlementsService(repo)
        plan_code, version, ents = service.get_entitlements(user_id)
        return EntitlementsOut(user_id=user_id, plan_code=plan_code, version=version, entitlements=ents)


