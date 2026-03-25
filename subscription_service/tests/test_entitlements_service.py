"""Tests for EntitlementsService and cache invalidation."""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.entitlements import (
    EntitlementsService,
    invalidate_entitlements_cache,
    _cache_key,
)
from app.utils.errors import ServiceError


class TestCacheKey:
    """Tests for _cache_key helper."""

    def test_format(self):
        key = _cache_key("user_123", 2)
        assert key == "ents:user_123:v2"

    def test_different_users_produce_different_keys(self):
        assert _cache_key("a", 1) != _cache_key("b", 1)

    def test_different_versions_produce_different_keys(self):
        assert _cache_key("a", 1) != _cache_key("a", 2)


class TestInvalidateEntitlementsCache:
    """Tests for invalidate_entitlements_cache module function."""

    def test_deletes_matching_keys(self, mock_redis):
        mock_redis.scan.return_value = (0, ["ents:user_1:v1", "ents:user_1:v2"])
        mock_redis.delete.return_value = 2

        deleted = invalidate_entitlements_cache("user_1", redis_client=mock_redis)

        assert deleted == 2
        mock_redis.delete.assert_called_once_with("ents:user_1:v1", "ents:user_1:v2")

    def test_no_keys_to_delete(self, mock_redis):
        mock_redis.scan.return_value = (0, [])

        deleted = invalidate_entitlements_cache("user_1", redis_client=mock_redis)

        assert deleted == 0
        mock_redis.delete.assert_not_called()

    def test_scan_uses_correct_pattern(self, mock_redis):
        mock_redis.scan.return_value = (0, [])

        invalidate_entitlements_cache("user_xyz", redis_client=mock_redis)

        mock_redis.scan.assert_called_once_with(
            cursor=0, match="ents:user_xyz:*", count=100
        )

    def test_handles_multi_page_scan(self, mock_redis):
        """Must iterate through multiple scan pages."""
        mock_redis.scan.side_effect = [
            (42, ["ents:user_1:v1"]),
            (0, ["ents:user_1:v2"]),
        ]
        mock_redis.delete.return_value = 1

        deleted = invalidate_entitlements_cache("user_1", redis_client=mock_redis)

        assert deleted == 2
        assert mock_redis.scan.call_count == 2


class TestEntitlementsService:
    """Tests for EntitlementsService.get_entitlements."""

    def test_returns_free_when_no_subscription(self, mock_redis):
        """User without subscription gets free plan with empty entitlements."""
        repo = MagicMock()
        repo.get_active_subscription.return_value = None

        service = EntitlementsService(repo, redis_client=mock_redis)
        plan_code, version, ents = service.get_entitlements("user_1")

        assert plan_code == "free"
        assert version == 1
        assert ents == {}

    def test_returns_cached_entitlements(self, mock_redis, make_subscription):
        """Must return cached data when available."""
        sub = make_subscription(plan_code="professional")
        repo = MagicMock()
        repo.get_active_subscription.return_value = sub
        repo.get_entitlements.return_value = (2, {"accounts": {"enabled": True, "limit_value": 10}})

        cached_data = {"accounts": {"enabled": True, "limit_value": 10}}
        mock_redis.get.return_value = json.dumps(cached_data)

        service = EntitlementsService(repo, redis_client=mock_redis)
        plan_code, version, ents = service.get_entitlements("user_1")

        assert plan_code == "professional"
        assert version == 2
        assert ents == cached_data

    def test_computes_and_caches_when_not_cached(self, mock_redis, make_subscription):
        """Must compute entitlements and store in cache when not cached."""
        sub = make_subscription(plan_code="professional")
        repo = MagicMock()
        repo.get_active_subscription.return_value = sub

        expected_ents = {"accounts": {"enabled": True, "limit_value": 10}}
        repo.get_entitlements.return_value = (2, expected_ents)
        mock_redis.get.return_value = None

        with patch("app.services.entitlements.settings") as mock_settings:
            mock_settings.ents_ttl_max = 300
            service = EntitlementsService(repo, redis_client=mock_redis)
            plan_code, version, ents = service.get_entitlements("user_1")

        assert plan_code == "professional"
        assert ents == expected_ents
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "ents:user_1:v2"
        assert call_args[0][1] == 300

    def test_raises_service_error_on_entitlements_failure(self, mock_redis, make_subscription):
        """Must raise ServiceError when entitlements lookup fails."""
        sub = make_subscription(plan_code="bad_plan")
        repo = MagicMock()
        repo.get_active_subscription.return_value = sub
        repo.get_entitlements.side_effect = Exception("DB error")

        service = EntitlementsService(repo, redis_client=mock_redis)

        with pytest.raises(ServiceError, match="Entitlements not available"):
            service.get_entitlements("user_1")


class TestEntitlementsServiceInvalidateCache:
    """Tests for EntitlementsService.invalidate_cache convenience method."""

    def test_delegates_to_module_function(self, mock_redis):
        repo = MagicMock()
        mock_redis.scan.return_value = (0, ["ents:user_1:v1"])
        mock_redis.delete.return_value = 1

        service = EntitlementsService(repo, redis_client=mock_redis)
        deleted = service.invalidate_cache("user_1")

        assert deleted == 1
