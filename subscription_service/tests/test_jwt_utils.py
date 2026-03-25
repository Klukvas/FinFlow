"""Tests for JWT utilities (enrich_jwt_claims, JtiDenyList)."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.utils.jwt import enrich_jwt_claims, JtiDenyList


class TestEnrichJwtClaims:
    """Tests for enrich_jwt_claims."""

    def test_adds_subscription_fields(self):
        base = {"sub": "user_1", "role": "user"}
        result = enrich_jwt_claims(
            base,
            plan_code="professional",
            expires_at_iso="2025-06-01T00:00:00",
            version=2,
        )

        assert result["sub_level"] == "professional"
        assert result["sub_exp"] == "2025-06-01T00:00:00"
        assert result["ents_version"] == 2
        # Original claims preserved
        assert result["sub"] == "user_1"
        assert result["role"] == "user"

    def test_does_not_mutate_original(self):
        """Must return a new dict, not mutate the original."""
        base = {"sub": "user_1"}
        result = enrich_jwt_claims(
            base,
            plan_code="basic",
            expires_at_iso=None,
            version=1,
        )

        assert "sub_level" not in base
        assert "sub_level" in result

    def test_none_expires_at_omits_sub_exp(self):
        """When expires_at_iso is None, sub_exp should not be set."""
        base = {"sub": "user_1"}
        result = enrich_jwt_claims(
            base,
            plan_code="free",
            expires_at_iso=None,
            version=1,
        )

        assert "sub_exp" not in result

    def test_empty_string_expires_at_is_included(self):
        """When expires_at_iso is empty string, sub_exp should not be set (falsy)."""
        base = {"sub": "user_1"}
        result = enrich_jwt_claims(
            base,
            plan_code="free",
            expires_at_iso="",
            version=1,
        )

        # Empty string is falsy, so sub_exp should not be set
        assert "sub_exp" not in result


class TestJtiDenyList:
    """Tests for JtiDenyList."""

    def test_deny_stores_marker(self):
        """deny must store a marker in Redis with TTL."""
        with patch("app.utils.jwt.redis") as mock_redis_module:
            mock_client = MagicMock()
            mock_redis_module.from_url.return_value = mock_client

            deny_list = JtiDenyList()
            deny_list.deny("jti_abc123", ttl_seconds=3600)

            mock_client.setex.assert_called_once_with(
                "denylist:jti:jti_abc123", 3600, "1"
            )

    def test_is_denied_returns_true_for_denied_jti(self):
        """is_denied must return True when JTI is in deny list."""
        with patch("app.utils.jwt.redis") as mock_redis_module:
            mock_client = MagicMock()
            mock_client.get.return_value = "1"
            mock_redis_module.from_url.return_value = mock_client

            deny_list = JtiDenyList()
            assert deny_list.is_denied("jti_abc123") is True

    def test_is_denied_returns_false_for_unknown_jti(self):
        """is_denied must return False when JTI is not in deny list."""
        with patch("app.utils.jwt.redis") as mock_redis_module:
            mock_client = MagicMock()
            mock_client.get.return_value = None
            mock_redis_module.from_url.return_value = mock_client

            deny_list = JtiDenyList()
            assert deny_list.is_denied("jti_unknown") is False
