"""
Unified SubscriptionClient for checking feature limits.

Replaces 9 per-service app/clients/subscription.py files.
Each service used a different method name (check_account_limit, check_expense_limit, etc.)
but the logic was identical. This version uses a generic check_limit(feature_code, ...) method.

Special methods for user_service (set_basic_plan) and workspace_service (get_feature_limit)
are also included.
"""

from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List, Set, Tuple

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)

_instance: Optional["SubscriptionClient"] = None


class SubscriptionClient:
    """Client for subscription_service feature/limit checks."""

    @classmethod
    def get_instance(cls) -> "SubscriptionClient":
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    _FEATURES_CACHE_TTL = 60  # seconds

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url or os.environ.get("SUBSCRIPTION_SERVICE_URL", "http://subscription_service:8080")
        ).rstrip("/")
        self.internal_token = os.environ.get("INTERNAL_SECRET_TOKEN", "")
        self.timeout = 5.0
        self.client = httpx.Client(timeout=self.timeout)
        self._features_cache: Dict[int, Tuple[Optional[Dict[str, Any]], float]] = {}  # user_id -> (features, expires_at)

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def get_user_features(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's feature entitlements (cached for 60s).

        Returns:
            dict mapping feature_code -> feature dict on success,
            {} on non-200 HTTP response,
            None on connection failure.
        """
        # Check cache
        cached = self._features_cache.get(user_id)
        if cached is not None:
            features, expires_at = cached
            if time.monotonic() < expires_at:
                return features

        url = f"{self.base_url}/v1/internal/features/{user_id}"
        try:
            resp = self.client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                features = {f["feature_code"]: f for f in resp.json()}
                self._features_cache[user_id] = (features, time.monotonic() + self._FEATURES_CACHE_TTL)
                return features
            logger.warning(f"Subscription service returned {resp.status_code} for user {user_id}")
            result: Optional[Dict[str, Any]] = {}
            self._features_cache[user_id] = (result, time.monotonic() + self._FEATURES_CACHE_TTL)
            return result
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Subscription service unreachable for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting features for user {user_id}: {e}")
            return None

    def check_limit(self, user_id: int, current_count: int, feature_code: str) -> Tuple[bool, Optional[int]]:
        """
        Generic limit check — replaces check_account_limit, check_expense_limit, etc.

        Fail-open: returns (True, None) when subscription service is unreachable.
        Returns (can_create, limit_value) so callers don't need to re-fetch features.
        """
        features = self.get_user_features(user_id)

        if features is None:
            logger.warning(
                f"Subscription service unreachable, allowing {feature_code} creation for user {user_id}"
            )
            return True, None

        feature = features.get(feature_code, {})

        if not feature:
            return False, 0

        if not feature.get("enabled", False):
            return False, 0

        limit = feature.get("limit_value")
        if limit is None:
            return True, None

        can_create = current_count < limit

        if not can_create:
            logger.info(f"User {user_id} reached {feature_code} limit: {current_count}/{limit}")

        return can_create, limit

    def get_feature_limit(self, user_id: int, feature_code: str) -> Optional[int]:
        """
        Get the limit value for a feature. Returns None for unlimited, 0 for disabled.

        Used by workspace_service's get_workspace_limit.
        """
        features = self.get_user_features(user_id)
        if features is None:
            return None

        feature = features.get(feature_code, {})
        if not feature.get("enabled", False):
            return 0

        return feature.get("limit_value")

    def set_basic_plan(self, user_id: int, plan_code: str = "basic") -> None:
        """
        Bootstrap a user with a subscription plan (used by user_service on registration).
        """
        url = f"{self.base_url}/v1/subscriptions/{user_id}:set_plan"
        headers = {
            "Idempotency-Key": f"user-{user_id}-bootstrap",
            "X-Internal-Token": self.internal_token,
        }
        payload = {"plan_code": plan_code}
        try:
            resp = self.client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logger.warning(
                    f"Failed to set {plan_code} plan for user {user_id}: status={resp.status_code}"
                )
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Subscription service unreachable when setting plan for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error setting plan for user {user_id}: {e}")

    def check_modify_allowed(
        self, user_id: int, record_id: Any, feature_code: str, ordered_record_ids: List
    ) -> bool:
        """
        Check if a record can be modified based on subscription limits.

        Oldest N records (by created_at) are editable; the rest are read-only.
        Fail-open: returns True when subscription service is unreachable.
        """
        features = self.get_user_features(user_id)
        if features is None:
            return True

        feature = features.get(feature_code, {})
        if not feature or not feature.get("enabled", False):
            return True

        limit = feature.get("limit_value")
        if limit is None:
            return True

        if len(ordered_record_ids) <= limit:
            return True

        allowed_ids = set(ordered_record_ids[:limit])
        return record_id in allowed_ids

    def get_read_only_ids(
        self, user_id: int, feature_code: str, ordered_record_ids: List
    ) -> Set:
        """
        Get IDs of records that are read-only due to plan limits.

        Returns empty set on error (fail-open).
        """
        features = self.get_user_features(user_id)
        if features is None:
            return set()

        feature = features.get(feature_code, {})
        if not feature or not feature.get("enabled", False):
            return set()

        limit = feature.get("limit_value")
        if limit is None or len(ordered_record_ids) <= limit:
            return set()

        return set(ordered_record_ids[limit:])

    def close(self):
        self.client.close()
