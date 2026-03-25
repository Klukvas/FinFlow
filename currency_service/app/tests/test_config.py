"""
Unit tests for configuration and settings.
"""
import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettings:
    def test_settings_loaded(self):
        """Settings should be importable and have default values."""
        from app.config import settings

        assert settings.api_title == "Currency Service"
        assert settings.api_version == "1.0.0"
        assert settings.currency_cache_ttl == 3600
        assert settings.fallback_cache_ttl == 86400
        assert settings.http_timeout == 10.0

    def test_cors_origins_list_wildcard(self):
        """When CORS_ORIGINS is *, cors_origins_list returns ['*']."""
        from app.config import settings

        if settings.cors_origins == "*":
            assert settings.cors_origins_list == ["*"]

    def test_cors_origins_list_multiple(self):
        """cors_origins_list splits comma-separated origins."""
        from app.config import settings

        original = settings.cors_origins
        try:
            # Temporarily override
            object.__setattr__(settings, "cors_origins", "http://a.com,http://b.com")
            result = settings.cors_origins_list
            assert result == ["http://a.com", "http://b.com"]
        finally:
            object.__setattr__(settings, "cors_origins", original)

    def test_redis_url_has_value(self):
        """Redis URL should be set."""
        from app.config import settings

        assert settings.redis_url
        assert "redis" in settings.redis_url

    def test_currency_api_url_has_value(self):
        """Currency API URL should be set."""
        from app.config import settings

        assert settings.currency_api_url
        assert "http" in settings.currency_api_url

    def test_internal_secret_token_validation(self):
        """Placeholder tokens should be rejected by the validator."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(internal_secret_token="your-internal-secret-token-here")

    def test_empty_secret_token_rejected(self):
        """Empty internal_secret_token should be rejected."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(internal_secret_token="")
