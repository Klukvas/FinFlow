"""Tests for application configuration."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from app.config import Settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_cors_origins_list_single(self):
        """Must parse single origin."""
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
            CORS_ORIGINS="http://localhost:3000",
        )
        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self):
        """Must parse comma-separated origins."""
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
            CORS_ORIGINS="http://localhost:3000,http://localhost:5173",
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

    def test_cors_origins_list_wildcard(self):
        """Must handle wildcard origin."""
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
            CORS_ORIGINS="*",
        )
        assert settings.cors_origins_list == ["*"]

    def test_cors_origins_list_strips_whitespace(self):
        """Must strip whitespace from origins."""
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
            CORS_ORIGINS="http://localhost:3000 , http://localhost:5173 ",
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

    def test_default_grace_period(self):
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
        )
        assert settings.grace_period_days == 3

    def test_default_ents_ttl(self):
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
        )
        assert settings.ents_ttl_min == 60
        assert settings.ents_ttl_max == 300

    def test_default_jwt_algorithm(self):
        settings = Settings(
            DATABASE_URL="postgresql://test:test@localhost/test",
        )
        assert settings.jwt_algorithm == "HS256"
