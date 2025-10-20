from __future__ import annotations

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class SubscriptionClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.SUBSCRIPTION_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def get_user_features(self, user_id: int) -> Dict[str, Any]:
        """Get user's feature entitlements"""
        url = f"{self.base_url}/v1/internal/features/{user_id}"
        headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
        try:
            resp = self.client.get(url, headers=headers)
            if resp.status_code == 200:
                features = resp.json()
                # Convert list to dict for easier lookup
                return {f["feature_code"]: f for f in features}
            return {}
        except Exception:
            return {}

    def check_recurring_limit(self, user_id: int, current_count: int) -> bool:
        """Check if user can create more recurring transactions"""
        features = self.get_user_features(user_id)
        recurring_feature = features.get("recurring", {})
        
        if not recurring_feature.get("enabled", False):
            return False
            
        limit = recurring_feature.get("limit_value")
        if limit is None:
            return True  # Unlimited
            
        return current_count < limit
