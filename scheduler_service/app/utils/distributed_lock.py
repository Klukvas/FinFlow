"""Redis-based distributed lock for scheduler job execution.

Prevents multiple scheduler instances from running the same job
concurrently in a multi-instance (e.g. Kubernetes) deployment.

Uses the SET NX EX pattern with a Lua script for safe release.
Uses redis.asyncio to avoid blocking the event loop.
"""
from __future__ import annotations

import uuid
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis

from ..config import settings

logger = logging.getLogger("scheduler_service.distributed_lock")

LOCK_KEY_PREFIX = "scheduler:lock:"
DEFAULT_LOCK_TTL_SECONDS = 600  # 10 minutes


class DistributedLock:
    """Async Redis distributed lock using SET NX EX pattern."""

    _RELEASE_LUA = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis = aioredis.from_url(
            redis_url or settings.REDIS_URL, decode_responses=True
        )
        self._instance_id = uuid.uuid4().hex

    async def acquire(self, lock_name: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> bool:
        """Try to acquire a named lock. Returns True if acquired."""
        key = f"{LOCK_KEY_PREFIX}{lock_name}"
        acquired = await self._redis.set(key, self._instance_id, nx=True, ex=ttl_seconds)
        if acquired:
            logger.info(
                f"Acquired distributed lock '{lock_name}'",
                extra={"instance": self._instance_id, "ttl": ttl_seconds},
            )
        return bool(acquired)

    async def release(self, lock_name: str) -> bool:
        """Release a lock only if this instance owns it (atomic via Lua)."""
        key = f"{LOCK_KEY_PREFIX}{lock_name}"
        result = await self._redis.eval(self._RELEASE_LUA, 1, key, self._instance_id)
        if result:
            logger.info(
                f"Released distributed lock '{lock_name}'",
                extra={"instance": self._instance_id},
            )
        return bool(result)

    @asynccontextmanager
    async def hold(
        self, lock_name: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS
    ) -> AsyncIterator[bool]:
        """Async context manager that yields True if lock was acquired."""
        acquired = await self.acquire(lock_name, ttl_seconds)
        try:
            yield acquired
        finally:
            if acquired:
                await self.release(lock_name)

    async def aclose(self) -> None:
        """Close the Redis connection pool."""
        await self._redis.aclose()
