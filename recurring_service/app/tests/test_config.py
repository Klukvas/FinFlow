"""Tests for Settings configuration."""
import os
import pytest
from unittest.mock import patch


class TestSettings:
    def test_settings_loads_from_environment(self):
        """Verify settings are loaded (already set in conftest.py env vars)."""
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token",
        }):
            s = Settings()
            assert s.DATABASE_URL == "sqlite:///:memory:"
            assert s.SECRET_KEY == "test-valid-secret-key"
            assert s.INTERNAL_SECRET_TOKEN == "test-valid-internal-token"

    def test_default_service_urls(self):
        """Verify default service URLs when not set in environment."""
        from app.config import Settings

        # Remove service URLs to test defaults, then restore
        env_override = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-2",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-2",
        }
        # Remove existing service URL env vars to get defaults
        keys_to_remove = [
            "EXPENSE_SERVICE_URL", "INCOME_SERVICE_URL", "CATEGORY_SERVICE_URL",
        ]
        saved = {k: os.environ.pop(k, None) for k in keys_to_remove}
        try:
            with patch.dict(os.environ, env_override):
                s = Settings()
                assert "expense_service" in s.EXPENSE_SERVICE_URL
                assert "income_service" in s.INCOME_SERVICE_URL
                assert "category_service" in s.CATEGORY_SERVICE_URL
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_default_algorithm(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-3",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-3",
        }):
            s = Settings()
            assert s.ALGORITHM == "HS256"

    def test_default_project_name(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-4",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-4",
        }):
            s = Settings()
            assert s.PROJECT_NAME == "Recurring Payments Service"

    def test_cors_origins_list_comma_separated(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-5",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-5",
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:5173",
        }):
            s = Settings()
            origins = s.cors_origins_list
            assert "http://localhost:3000" in origins
            assert "http://localhost:5173" in origins

    def test_cors_origins_list_wildcard(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-6",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-6",
            "CORS_ORIGINS": "*",
        }):
            s = Settings()
            assert s.cors_origins_list == ["*"]

    def test_rejects_placeholder_secret_key(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "your-secret-key-here",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-7",
        }):
            with pytest.raises(Exception):
                Settings()

    def test_rejects_placeholder_internal_token(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-8",
            "INTERNAL_SECRET_TOKEN": "your-internal-secret-token-here",
        }):
            with pytest.raises(Exception):
                Settings()

    def test_rejects_empty_secret_key(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-9",
        }):
            with pytest.raises(Exception):
                Settings()

    def test_rejects_empty_internal_token(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-10",
            "INTERNAL_SECRET_TOKEN": "",
        }):
            with pytest.raises(Exception):
                Settings()

    def test_default_log_level(self):
        from app.config import Settings

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-valid-secret-key-11",
            "INTERNAL_SECRET_TOKEN": "test-valid-internal-token-11",
        }):
            s = Settings()
            assert s.LOG_LEVEL == "INFO"
