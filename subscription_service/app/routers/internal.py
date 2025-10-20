from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.features import FeatureRepository
from ..schemas.features import UserFeatureOut
from ..utils.errors import AuthError


router = APIRouter()


from ..config import settings


def verify_internal_token(internal_token: str = Header(alias="X-Internal-Token")) -> None:
    """Verify internal service token"""
    if internal_token != settings.internal_secret_token:
        raise AuthError("Invalid internal token", error_code="@subscription_service/INVALID_INTERNAL_TOKEN")


@router.get("/internal/features/{user_id}", response_model=list[UserFeatureOut])
def get_user_features_internal(
    user_id: str, 
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint for other services to get user's feature entitlements"""
    repo = FeatureRepository(db)
    user_features = repo.get_user_features(user_id)
    return [UserFeatureOut(**uf) for uf in user_features]
