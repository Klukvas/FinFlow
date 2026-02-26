from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional
import redis

from ..config import settings
from ..repositories.subscriptions import SubscriptionRepository
from ..utils.errors import ServiceError

logger = logging.getLogger("subscription_service.entitlements")

_CACHE_PREFIX = "ents:"


def _cache_key(user_id: str, version: int) -> str:
    return f"{_CACHE_PREFIX}{user_id}:v{version}"


def _get_default_redis() -> redis.Redis:
    """Return a shared Redis client (lazily initialised)."""
    return redis.from_url(settings.redis_url, decode_responses=True)


def invalidate_entitlements_cache(user_id: str, redis_client: Optional[redis.Redis] = None) -> int:
    """Delete all entitlements cache entries for *user_id*.

    Uses SCAN with a pattern to avoid blocking the server with KEYS on
    large keyspaces.  Returns the number of keys deleted.
    """
    r = redis_client or _get_default_redis()
    pattern = f"{_CACHE_PREFIX}{user_id}:*"
    deleted = 0
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            deleted += r.delete(*keys)
        if cursor == 0:
            break
    if deleted:
        logger.info(
            f"Invalidated {deleted} entitlements cache key(s) for user {user_id}",
            extra={"user_id": user_id, "deleted_keys": deleted},
        )
    return deleted


class EntitlementsService:
    def __init__(self, repo: SubscriptionRepository, redis_client: Optional[redis.Redis] = None) -> None:
        self.repo = repo
        self.redis = redis_client or _get_default_redis()

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
        ttl = settings.ents_ttl_max
        self.redis.setex(key, ttl, json.dumps(ents))
        return sub.plan_code, version, ents

    def invalidate_cache(self, user_id: str) -> int:
        """Convenience wrapper around the module-level function."""
        return invalidate_entitlements_cache(user_id, self.redis)


