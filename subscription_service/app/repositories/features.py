from __future__ import annotations

from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import Feature, PlanFeature, Plan
from ..repositories.subscriptions import SubscriptionRepository


class FeatureRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> List[Feature]:
        return self.db.query(Feature).order_by(Feature.code.asc()).all()

    def get_by_code(self, code: str) -> Optional[Feature]:
        return self.db.query(Feature).filter(Feature.code == code).first()

    def get_plan_features(self, plan_code: str) -> List[PlanFeature]:
        return (
            self.db.query(PlanFeature)
            .join(Plan, Plan.id == PlanFeature.plan_id)
            .filter(Plan.code == plan_code)
            .all()
        )

    def get_user_features(self, user_id: str) -> List[dict]:
        """Get user's feature entitlements with plan context"""
        repo = SubscriptionRepository(self.db)
        sub = repo.get_active_subscription(user_id)
        if sub is None:
            return []
        
        plan_features = self.get_plan_features(sub.plan_code)
        return [
            {
                "feature_code": pf.feature_code,
                "enabled": pf.enabled,
                "limit_value": pf.limit_value,
                "plan_code": sub.plan_code
            }
            for pf in plan_features
        ]
