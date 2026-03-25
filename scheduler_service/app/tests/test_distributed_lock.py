"""Tests for the Redis-based DistributedLock.

Redis calls are mocked so tests run without a real Redis instance.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.utils.distributed_lock import (
    DistributedLock,
    LOCK_KEY_PREFIX,
    DEFAULT_LOCK_TTL_SECONDS,
)


@pytest.fixture()
def mock_redis():
    """AsyncMock that mimics redis.asyncio client."""
    r = AsyncMock()
    r.set = AsyncMock(return_value=True)
    r.eval = AsyncMock(return_value=1)
    r.aclose = AsyncMock()
    return r


@pytest.fixture()
def lock(mock_redis):
    """DistributedLock with injected mock Redis."""
    with patch("app.utils.distributed_lock.aioredis") as mock_aioredis:
        mock_aioredis.from_url.return_value = mock_redis
        dl = DistributedLock(redis_url="redis://fake:6379/0")
    return dl


class TestAcquire:
    @pytest.mark.asyncio
    async def test_acquire_succeeds(self, lock, mock_redis):
        mock_redis.set.return_value = True

        result = await lock.acquire("test_lock")

        assert result is True
        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args.kwargs
        assert call_kwargs["nx"] is True
        assert call_kwargs["ex"] == DEFAULT_LOCK_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_acquire_fails_when_already_held(self, lock, mock_redis):
        mock_redis.set.return_value = None  # Redis SET NX returns None if key exists

        result = await lock.acquire("test_lock")

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_uses_correct_key(self, lock, mock_redis):
        mock_redis.set.return_value = True

        await lock.acquire("my_job")

        call_args = mock_redis.set.call_args
        key = call_args[0][0]
        assert key == f"{LOCK_KEY_PREFIX}my_job"

    @pytest.mark.asyncio
    async def test_acquire_with_custom_ttl(self, lock, mock_redis):
        mock_redis.set.return_value = True

        await lock.acquire("test_lock", ttl_seconds=120)

        call_kwargs = mock_redis.set.call_args.kwargs
        assert call_kwargs["ex"] == 120

    @pytest.mark.asyncio
    async def test_acquire_stores_instance_id(self, lock, mock_redis):
        mock_redis.set.return_value = True

        await lock.acquire("test_lock")

        call_args = mock_redis.set.call_args
        value = call_args[0][1]
        assert value == lock._instance_id


class TestRelease:
    @pytest.mark.asyncio
    async def test_release_succeeds(self, lock, mock_redis):
        mock_redis.eval.return_value = 1

        result = await lock.release("test_lock")

        assert result is True
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_fails_when_not_owner(self, lock, mock_redis):
        mock_redis.eval.return_value = 0  # Lua script returns 0 if not owner

        result = await lock.release("test_lock")

        assert result is False

    @pytest.mark.asyncio
    async def test_release_uses_correct_key(self, lock, mock_redis):
        mock_redis.eval.return_value = 1

        await lock.release("my_job")

        call_args = mock_redis.eval.call_args
        # eval(script, num_keys, key, value)
        key_arg = call_args[0][2]
        assert key_arg == f"{LOCK_KEY_PREFIX}my_job"

    @pytest.mark.asyncio
    async def test_release_uses_lua_script(self, lock, mock_redis):
        mock_redis.eval.return_value = 1

        await lock.release("test_lock")

        call_args = mock_redis.eval.call_args
        lua_script = call_args[0][0]
        assert "redis.call" in lua_script
        assert "del" in lua_script


class TestHoldContextManager:
    @pytest.mark.asyncio
    async def test_yields_true_when_acquired(self, lock, mock_redis):
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        async with lock.hold("test_lock") as acquired:
            assert acquired is True

        # Lock should be released after context exits
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_yields_false_when_not_acquired(self, lock, mock_redis):
        mock_redis.set.return_value = None

        async with lock.hold("test_lock") as acquired:
            assert acquired is False

        # Release should NOT be called when lock was not acquired
        mock_redis.eval.assert_not_called()

    @pytest.mark.asyncio
    async def test_releases_on_exception(self, lock, mock_redis):
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        with pytest.raises(ValueError):
            async with lock.hold("test_lock") as acquired:
                assert acquired is True
                raise ValueError("boom")

        # Lock must still be released
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_hold_passes_ttl(self, lock, mock_redis):
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        async with lock.hold("test_lock", ttl_seconds=30):
            pass

        call_kwargs = mock_redis.set.call_args.kwargs
        assert call_kwargs["ex"] == 30


class TestAclose:
    @pytest.mark.asyncio
    async def test_closes_redis_connection(self, lock, mock_redis):
        await lock.aclose()

        mock_redis.aclose.assert_called_once()


class TestInstanceId:
    def test_unique_instance_ids(self):
        """Each DistributedLock instance should have a unique ID."""
        with patch("app.utils.distributed_lock.aioredis") as mock_aioredis:
            mock_aioredis.from_url.return_value = AsyncMock()
            lock1 = DistributedLock(redis_url="redis://fake:6379/0")
            lock2 = DistributedLock(redis_url="redis://fake:6379/0")

        assert lock1._instance_id != lock2._instance_id
        assert len(lock1._instance_id) == 32  # uuid4().hex length
