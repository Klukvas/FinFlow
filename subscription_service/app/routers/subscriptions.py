from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.subscriptions import SubscriptionService
from ..repositories.subscriptions import SubscriptionRepository
from ..schemas.subscription import SetPlanIn, SubscriptionOut
from ..utils.errors import ConflictError, NotFoundError
from ..utils.idempotency import IdempotencyStore


router = APIRouter()

_IDEMPOTENCY_KEYS: dict[str, str] = {}


@router.get("/subscriptions/{user_id}", response_model=SubscriptionOut)
def get_subscription(user_id: str, db: Session = Depends(get_db)):
    """Get user's current subscription"""
    repo = SubscriptionRepository(db)
    subscription = repo.get_active_subscription(user_id)
    
    if subscription is None:
        raise NotFoundError("Subscription not found", error_code="@subscription_service/SUBSCRIPTION_NOT_FOUND")
    
    return SubscriptionOut.model_validate(subscription, from_attributes=True)


@router.post("/subscriptions/{user_id}:set_plan", response_model=SubscriptionOut)
def set_plan(user_id: str, payload: SetPlanIn, db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if idempotency_key:
        store = IdempotencyStore()
        ok = store.check_and_set(idempotency_key, f"{user_id}:{payload.plan_code}")
        if not ok:
            raise ConflictError("Idempotency-Key conflict", error_code="@subscription_service/IDEMPOTENCY_VIOLATION")

    service = SubscriptionService(db)
    sub = service.set_plan(user_id, payload.plan_code, payload.status)
    return SubscriptionOut.model_validate(sub, from_attributes=True)


