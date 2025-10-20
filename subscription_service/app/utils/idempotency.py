from __future__ import annotations

import redis
from typing import Optional

from ..config import settings


class IdempotencyStore:
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        self.redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)

    def check_and_set(self, key: str, value: str, ttl_seconds: int = 3600) -> bool:
        # returns True if set, False if conflict
        with self.redis.pipeline() as pipe:
            try:
                pipe.watch(key)
                existing = pipe.get(key)
                if existing is None:
                    pipe.multi()
                    pipe.setex(key, ttl_seconds, value)
                    pipe.execute()
                    return True
                return existing == value
            finally:
                pipe.reset()


