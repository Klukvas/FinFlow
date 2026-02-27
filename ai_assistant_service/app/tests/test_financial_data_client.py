"""Tests for financial data client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

import httpx

from app.clients.financial_data_client import fetch_data, SERVICE_URLS, ENDPOINT_PATHS


TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


class TestServiceUrls:
    def test_all_services_have_urls(self):
        expected = {"expenses", "incomes", "debts", "goals", "accounts", "categories", "recurring"}
        assert set(SERVICE_URLS.keys()) == expected

    def test_all_services_have_endpoint_paths(self):
        expected = {"expenses", "incomes", "debts", "goals", "accounts", "categories", "recurring"}
        assert set(ENDPOINT_PATHS.keys()) == expected

    def test_endpoint_paths_format(self):
        for source, path in ENDPOINT_PATHS.items():
            assert path.startswith("/internal/")
            assert path.endswith("/ai-summary")


class TestFetchData:
    async def test_successful_fetch(self, mock_httpx_response):
        response_data = {"items": [{"amount": 100}]}
        mock_response = mock_httpx_response(200, response_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_data("expenses", TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result == response_data
        mock_client.get.assert_called_once()

    async def test_non_200_returns_none(self, mock_httpx_response):
        mock_response = mock_httpx_response(500)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_data("expenses", TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result is None

    async def test_timeout_returns_none(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_data("expenses", TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result is None

    async def test_network_error_returns_none(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_data("incomes", TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result is None

    async def test_unknown_source_returns_none(self):
        result = await fetch_data("unknown_source", TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result is None

    async def test_sends_correct_headers(self, mock_httpx_response):
        mock_response = mock_httpx_response(200, {"items": []})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await fetch_data("expenses", TEST_USER_ID, TEST_WORKSPACE_ID)

        call_kwargs = mock_client.get.call_args[1]
        assert "X-Internal-Token" in call_kwargs["headers"]
        assert call_kwargs["params"]["user_id"] == str(TEST_USER_ID)
        assert call_kwargs["params"]["workspace_id"] == str(TEST_WORKSPACE_ID)
