from __future__ import annotations

import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.SUBSCRIPTION_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if settings.INTERNAL_SECRET_TOKEN:
            headers["X-Internal-Token"] = settings.INTERNAL_SECRET_TOKEN
        return headers

    def get_user_features(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's feature entitlements. Returns None on connection failure, {} on empty response."""
        url = f"{self.base_url}/v1/internal/features/{user_id}"
        try:
            resp = self.client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                features = resp.json()
                return {f["feature_code"]: f for f in features}
            logger.warning(f"Subscription service returned {resp.status_code} for user {user_id}")
            return {}
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Subscription service unreachable for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting features for user {user_id}: {e}")
            return None

    def check_category_limit(self, user_id: int, current_count: int) -> bool:
        """Check if user can create more categories"""
        features = self.get_user_features(user_id)

        if features is None:
            logger.warning(f"Subscription service unreachable, allowing category creation for user {user_id}")
            return True

        category_feature = features.get("categories", {})

        if not category_feature.get("enabled", False):
            return False

        limit = category_feature.get("limit_value")
        if limit is None:
            return True

        return current_count < limit
