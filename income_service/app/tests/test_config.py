"""Tests for app/config.py — Settings validation."""
import os
import pytest
from unittest.mock import patch

from pydantic import ValidationError


class TestSettings:
    def test_settings_loads_from_env(self):
        """Settings should load correctly from environment."""
        from app.config import settings

        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM == "HS256"
        assert settings.INTERNAL_SECRET_TOKEN is not None

    def test_default_values(self):
        from app.config import settings

        assert settings.MAX_AMOUNT == 999999.99
        assert settings.MAX_DESCRIPTION_LENGTH == 500
        assert settings.DEFAULT_CURRENCY == "USD"
        assert settings.HTTP_TIMEOUT == 5.0
        assert settings.HTTP_RETRY_ATTEMPTS == 3
        assert settings.LOG_LEVEL == "INFO"

    def test_cors_origins_list_comma_separated(self):
        from app.config import settings

        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) > 0
        for origin in origins:
            assert origin.strip() == origin  # no leading/trailing whitespace

    def test_cors_origins_list_wildcard(self):
        """When CORS_ORIGINS is '*', cors_origins_list returns ['*']."""
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "valid-secret-key-123",
            "INTERNAL_SECRET_TOKEN": "valid-internal-token-123",
            "CORS_ORIGINS": "*",
        }
        with patch.dict(os.environ, env, clear=False):
            s = Settings(**env)
            assert s.cors_origins_list == ["*"]

    def test_external_service_urls_have_defaults(self):
        from app.config import settings

        assert "user_service" in settings.USER_SERVICE_URL or "localhost" in settings.USER_SERVICE_URL
        assert "category_service" in settings.CATEGORY_SERVICE_URL or "localhost" in settings.CATEGORY_SERVICE_URL
        assert "account_service" in settings.ACCOUNT_SERVICE_URL or "localhost" in settings.ACCOUNT_SERVICE_URL

    def test_placeholder_secret_key_rejected(self):
        """Settings should reject placeholder secret keys."""
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "your-secret-key-here",
            "INTERNAL_SECRET_TOKEN": "valid-token-xyz",
        }
        with pytest.raises(ValidationError) as exc_info:
            Settings(**env)
        assert "SECRET_KEY" in str(exc_info.value)

    def test_placeholder_internal_token_rejected(self):
        """Settings should reject placeholder internal tokens."""
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "valid-secret-key-123",
            "INTERNAL_SECRET_TOKEN": "my-secret-token",
        }
        with pytest.raises(ValidationError) as exc_info:
            Settings(**env)
        assert "INTERNAL_SECRET_TOKEN" in str(exc_info.value)

    def test_empty_secret_key_rejected(self):
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "",
            "INTERNAL_SECRET_TOKEN": "valid-token-xyz",
        }
        with pytest.raises(ValidationError):
            Settings(**env)

    def test_empty_internal_token_rejected(self):
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "valid-secret-key-123",
            "INTERNAL_SECRET_TOKEN": "",
        }
        with pytest.raises(ValidationError):
            Settings(**env)

    def test_valid_settings_pass_validation(self):
        from app.config import Settings

        env = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "production-strong-secret-key",
            "INTERNAL_SECRET_TOKEN": "production-strong-token",
        }
        s = Settings(**env)
        assert s.SECRET_KEY == "production-strong-secret-key"
        assert s.INTERNAL_SECRET_TOKEN == "production-strong-token"
