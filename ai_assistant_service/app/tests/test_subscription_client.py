"""Tests for subscription client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.subscription_client import check_feature_access, ALLOWED_PLANS


class TestAllowedPlans:
    def test_professional_allowed(self):
        assert "professional" in ALLOWED_PLANS

    def test_enterprise_allowed(self):
        assert "enterprise" in ALLOWED_PLANS

    def test_basic_not_allowed(self):
        assert "basic" not in ALLOWED_PLANS


class TestCheckFeatureAccess:
    async def test_professional_plan_returns_plan_code(self):
        features = [
            {"feature_code": "ai_assistant", "enabled": True, "plan_code": "professional"},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = features

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result == "professional"

    async def test_enterprise_plan_returns_plan_code(self):
        features = [
            {"feature_code": "ai_assistant", "enabled": True, "plan_code": "enterprise"},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = features

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result == "enterprise"

    async def test_basic_plan_returns_none(self):
        features = [
            {"feature_code": "ai_assistant", "enabled": True, "plan_code": "basic"},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = features

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result is None

    async def test_disabled_feature_returns_none(self):
        features = [
            {"feature_code": "ai_assistant", "enabled": False, "plan_code": "professional"},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = features

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result is None

    async def test_missing_feature_returns_none(self):
        features = [
            {"feature_code": "some_other_feature", "enabled": True, "plan_code": "professional"},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = features

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result is None

    async def test_service_error_returns_none(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result is None

    async def test_network_error_returns_none(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_feature_access(42)

        assert result is None
