"""Tests for rate limiter service."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services import rate_limiter


class TestCooldownKey:
    def test_key_format(self):
        key = rate_limiter._cooldown_key(42, "ws-123", "expenses_reduce_spending")
        assert key == "ai_cooldown:42:ws-123:expenses_reduce_spending"

    def test_key_includes_workspace_id(self):
        key1 = rate_limiter._cooldown_key(42, "ws-1", "prompt-1")
        key2 = rate_limiter._cooldown_key(42, "ws-2", "prompt-1")
        assert key1 != key2


class TestPlanCooldowns:
    def test_professional_cooldown(self):
        assert rate_limiter.PLAN_COOLDOWNS["professional"] == 604800  # 7 days

    def test_enterprise_cooldown(self):
        assert rate_limiter.PLAN_COOLDOWNS["enterprise"] == 259200  # 3 days


class TestCheckRateLimit:
    async def test_allowed_when_no_existing_key(self, mock_redis):
        mock_redis.ttl = AsyncMock(return_value=-2)  # key doesn't exist

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "professional")

        assert result is None

    async def test_rate_limited_when_key_exists(self, mock_redis):
        mock_redis.ttl = AsyncMock(return_value=3600)  # 1 hour remaining

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "professional")

        assert result == 3600

    async def test_unknown_plan_returns_max_cooldown(self, mock_redis):
        result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "basic")
        assert result == 604800

    async def test_redis_error_fails_closed(self, mock_redis):
        mock_redis.ttl = AsyncMock(side_effect=Exception("Redis error"))

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "professional")

        # Fails closed - denies for 60 seconds
        assert result == 60

    async def test_ttl_zero_means_allowed(self, mock_redis):
        mock_redis.ttl = AsyncMock(return_value=0)

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "enterprise")

        assert result is None

    async def test_ttl_negative_means_allowed(self, mock_redis):
        mock_redis.ttl = AsyncMock(return_value=-1)  # key exists but no TTL

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            result = await rate_limiter.check_rate_limit(42, "ws-1", "prompt-1", "enterprise")

        assert result is None


class TestSetRateLimit:
    async def test_sets_key_with_professional_ttl(self, mock_redis):
        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            await rate_limiter.set_rate_limit(42, "ws-1", "prompt-1", "professional")

        mock_redis.set.assert_called_once_with(
            "ai_cooldown:42:ws-1:prompt-1", "1", ex=604800
        )

    async def test_sets_key_with_enterprise_ttl(self, mock_redis):
        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            await rate_limiter.set_rate_limit(42, "ws-1", "prompt-1", "enterprise")

        mock_redis.set.assert_called_once_with(
            "ai_cooldown:42:ws-1:prompt-1", "1", ex=259200
        )

    async def test_unknown_plan_does_nothing(self, mock_redis):
        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            await rate_limiter.set_rate_limit(42, "ws-1", "prompt-1", "basic")

        mock_redis.set.assert_not_called()

    async def test_redis_error_does_not_raise(self, mock_redis):
        mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))

        with patch("app.services.rate_limiter.get_redis", return_value=mock_redis):
            # Should not raise
            await rate_limiter.set_rate_limit(42, "ws-1", "prompt-1", "professional")
