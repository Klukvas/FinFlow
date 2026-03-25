"""
Unit tests for Settings configuration.

Tests cover:
- Settings validation (model_validator for secrets)
- cors_origins_list property
- Default values
"""
import os
import pytest
from unittest.mock import patch

from pydantic import ValidationError


class TestSettingsValidation:
    """Tests for Settings secret validation."""

    def _make_settings(self, **overrides):
        """Build a Settings instance with defaults + overrides."""
        # Import Settings fresh so the module-level `settings` singleton
        # does not interfere.
        from app.config import Settings

        defaults = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "real-strong-key-abc123",
            "INTERNAL_SECRET_TOKEN": "real-strong-token-xyz789",
        }
        defaults.update(overrides)
        return Settings(**defaults)

    def test_valid_settings(self):
        s = self._make_settings()
        assert s.ALGORITHM == "HS256"
        assert s.LOG_LEVEL == "INFO"
        assert s.INVITE_EXPIRE_DAYS == 3

    def test_placeholder_secret_key_raises(self):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            self._make_settings(SECRET_KEY="your-secret-key-here")

    def test_placeholder_internal_token_raises(self):
        with pytest.raises(ValidationError, match="INTERNAL_SECRET_TOKEN"):
            self._make_settings(INTERNAL_SECRET_TOKEN="your-internal-secret-token-here")

    def test_empty_secret_key_raises(self):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            self._make_settings(SECRET_KEY="")

    def test_empty_internal_token_raises(self):
        with pytest.raises(ValidationError, match="INTERNAL_SECRET_TOKEN"):
            self._make_settings(INTERNAL_SECRET_TOKEN="")

    def test_changeme_secret_key_raises(self):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            self._make_settings(SECRET_KEY="changeme-in-production")

    def test_changeme_internal_token_raises(self):
        with pytest.raises(ValidationError, match="INTERNAL_SECRET_TOKEN"):
            self._make_settings(INTERNAL_SECRET_TOKEN="my-secret-token")

    def test_user_service_url_is_set(self):
        s = self._make_settings()
        assert s.USER_SERVICE_URL.startswith("http")

    def test_subscription_service_url_is_set(self):
        s = self._make_settings()
        assert s.SUBSCRIPTION_SERVICE_URL.startswith("http")


class TestCorsOriginsList:
    """Tests for Settings.cors_origins_list property."""

    def _make_settings(self, cors: str = None):
        from app.config import Settings

        kwargs = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "real-strong-key-abc123",
            "INTERNAL_SECRET_TOKEN": "real-strong-token-xyz789",
        }
        if cors is not None:
            kwargs["CORS_ORIGINS"] = cors
        return Settings(**kwargs)

    def test_default_origins(self):
        s = self._make_settings()
        origins = s.cors_origins_list
        assert isinstance(origins, list)
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins

    def test_wildcard(self):
        s = self._make_settings(cors="*")
        assert s.cors_origins_list == ["*"]

    def test_single_origin(self):
        s = self._make_settings(cors="http://example.com")
        assert s.cors_origins_list == ["http://example.com"]

    def test_multiple_origins_trimmed(self):
        s = self._make_settings(cors=" http://a.com , http://b.com ")
        origins = s.cors_origins_list
        assert "http://a.com" in origins
        assert "http://b.com" in origins
