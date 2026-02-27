"""Tests for Redis cache service."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services import cache_service


class TestCacheKey:
    def test_cache_key_format(self):
        key = cache_service._cache_key("ws-123", "expenses_reduce_spending", "ru", "abc123")
        assert key == "ai:ws-123:expenses_reduce_spending:ru:abc123"

    def test_cache_key_with_uuid(self):
        key = cache_service._cache_key(
            "550e8400-e29b-41d4-a716-446655440000",
            "debts_pay_first",
            "en",
            "def456",
        )
        assert key == "ai:550e8400-e29b-41d4-a716-446655440000:debts_pay_first:en:def456"

    def test_cache_key_different_languages(self):
        key_ru = cache_service._cache_key("ws-1", "prompt-1", "ru", "hash-1")
        key_en = cache_service._cache_key("ws-1", "prompt-1", "en", "hash-1")
        assert key_ru != key_en


class TestGetCachedResult:
    async def test_cache_hit_returns_parsed_json(self, mock_redis):
        cached_data = {"sections": [{"title": "Test", "content": "Content", "priority": "high"}]}
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        with patch.object(cache_service, "get_redis", return_value=mock_redis):
            result = await cache_service.get_cached_result("ws-1", "prompt-1", "ru", "hash-1")

        assert result == cached_data
        mock_redis.get.assert_called_once_with("ai:ws-1:prompt-1:ru:hash-1")

    async def test_cache_miss_returns_none(self, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)

        with patch.object(cache_service, "get_redis", return_value=mock_redis):
            result = await cache_service.get_cached_result("ws-1", "prompt-1", "en", "hash-1")

        assert result is None

    async def test_cache_error_returns_none(self, mock_redis):
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))

        with patch.object(cache_service, "get_redis", return_value=mock_redis):
            result = await cache_service.get_cached_result("ws-1", "prompt-1", "uk", "hash-1")

        assert result is None


class TestSetCachedResult:
    async def test_set_stores_with_ttl(self, mock_redis):
        data = {"sections": [{"title": "Test", "content": "Content"}]}

        with patch.object(cache_service, "get_redis", return_value=mock_redis):
            await cache_service.set_cached_result("ws-1", "prompt-1", "ru", "hash-1", data)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "ai:ws-1:prompt-1:ru:hash-1"
        assert json.loads(call_args[0][1]) == data
        assert call_args[1]["ex"] == cache_service.settings.CACHE_TTL

    async def test_set_error_does_not_raise(self, mock_redis):
        mock_redis.set = AsyncMock(side_effect=Exception("Redis write error"))

        with patch.object(cache_service, "get_redis", return_value=mock_redis):
            # Should not raise
            await cache_service.set_cached_result("ws-1", "prompt-1", "en", "hash-1", {"data": "test"})


class TestGetRedis:
    async def test_creates_client_once(self):
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            client1 = await cache_service.get_redis()
            client2 = await cache_service.get_redis()

            assert client1 is client2
            mock_from_url.assert_called_once()


class TestCloseRedis:
    async def test_close_clears_singleton(self, mock_redis):
        cache_service._redis_client = mock_redis
        await cache_service.close_redis()
        assert cache_service._redis_client is None
        mock_redis.close.assert_called_once()

    async def test_close_when_no_client(self):
        cache_service._redis_client = None
        # Should not raise
        await cache_service.close_redis()
