from __future__ import annotations

import json
from datetime import datetime
from typing import Optional
import redis

from ..config import settings
from ..repositories.subscriptions import SubscriptionRepository
from ..utils.errors import ServiceError


def _cache_key(user_id: str, version: int) -> str:
    return f"ents:{user_id}:v{version}"


class EntitlementsService:
    def __init__(self, repo: SubscriptionRepository, redis_client: Optional[redis.Redis] = None) -> None:
        self.repo = repo
        self.redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)

    def get_entitlements(self, user_id: str) -> tuple[str, int, dict]:
        sub = self.repo.get_active_subscription(user_id)
        if sub is None:
            return "free", 1, {}

        try:
            version, ents = self.repo.get_entitlements(sub.plan_code)
        except Exception:
            # Surface a well-formed service error
            raise ServiceError(
                "Entitlements not available",
                error_code="@subscription_service/ENTITLEMENTS_NOT_AVAILABLE",
                status_code=503,
            )
        key = _cache_key(user_id, version)

        # try cache
        cached = self.redis.get(key)
        if cached:
            data = json.loads(cached)
            return sub.plan_code, version, data

        # compute and store
        ttl = max(min(settings.ents_ttl_max, settings.ents_ttl_min), settings.ents_ttl_min)
        self.redis.setex(key, ttl, json.dumps(ents))
        return sub.plan_code, version, ents


