"""Tests for app/services/monobank_client.py - MonobankClient and helpers."""

import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.monobank_client import (
    MonobankClient,
    numeric_to_alpha_currency,
    CURRENCY_MAP,
)
from app.exceptions import MonobankApiError, RateLimitError
from app.schemas.monobank import MonobankClientInfo, MonobankStatementItem


class TestNumericToAlphaCurrency:
    """Tests for the numeric_to_alpha_currency utility."""

    def test_uah(self):
        assert numeric_to_alpha_currency(980) == "UAH"

    def test_usd(self):
        assert numeric_to_alpha_currency(840) == "USD"

    def test_eur(self):
        assert numeric_to_alpha_currency(978) == "EUR"

    def test_gbp(self):
        assert numeric_to_alpha_currency(826) == "GBP"

    def test_pln(self):
        assert numeric_to_alpha_currency(985) == "PLN"

    def test_unknown_code_returns_string_of_code(self):
        assert numeric_to_alpha_currency(9999) == "9999"

    def test_all_known_currencies_covered(self):
        for code, alpha in CURRENCY_MAP.items():
            assert numeric_to_alpha_currency(code) == alpha


class TestMonobankClientRateLimit:
    """Tests for rate limit logic in MonobankClient."""

    def test_check_rate_limit_raises_when_too_soon(self):
        client = MonobankClient()
        token = "test-token"
        # Simulate a recent request
        key = client._token_key(token)
        client._last_request_time[key] = time.time()

        with pytest.raises(RateLimitError):
            client._check_rate_limit(token)

    def test_check_rate_limit_passes_after_cooldown(self):
        client = MonobankClient()
        token = "test-token"
        key = client._token_key(token)
        # Set last request to well in the past
        client._last_request_time[key] = time.time() - 120

        # Should not raise
        client._check_rate_limit(token)

    def test_check_rate_limit_passes_with_no_prior_request(self):
        client = MonobankClient()
        # No prior request recorded; should not raise
        client._check_rate_limit("fresh-token")

    def test_record_request_updates_timestamp(self):
        client = MonobankClient()
        token = "test-token"
        key = client._token_key(token)
        before = time.time()
        client._record_request(token)
        after = time.time()

        assert key in client._last_request_time
        assert before <= client._last_request_time[key] <= after

    def test_token_key_is_deterministic(self):
        client = MonobankClient()
        assert client._token_key("abc") == client._token_key("abc")

    def test_different_tokens_produce_different_keys(self):
        client = MonobankClient()
        assert client._token_key("token1") != client._token_key("token2")


class TestMonobankClientGetClientInfo:
    """Tests for MonobankClient.get_client_info."""

    @pytest.mark.asyncio
    async def test_successful_get_client_info(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response_data = {
            "clientId": "abc123",
            "name": "Test User",
            "webHookUrl": "",
            "permissions": "p",
            "accounts": [
                {
                    "id": "acc1",
                    "balance": 10000,
                    "creditLimit": 0,
                    "currencyCode": 980,
                    "type": "black",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.get_client_info("valid-token")

        assert isinstance(result, MonobankClientInfo)
        assert result.name == "Test User"
        assert len(result.accounts) == 1

    @pytest.mark.asyncio
    async def test_get_client_info_forbidden_raises_monobank_api_error(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            with pytest.raises(MonobankApiError):
                await client.get_client_info("bad-token")

    @pytest.mark.asyncio
    async def test_get_client_info_429_raises_rate_limit_error(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            with pytest.raises(RateLimitError):
                await client.get_client_info("token")

    @pytest.mark.asyncio
    async def test_get_client_info_request_error_raises_monobank_api_error(self):
        client = MonobankClient()
        client._last_request_time.clear()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("Connection failed")
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            with pytest.raises(MonobankApiError, match="Failed to connect"):
                await client.get_client_info("token")

    @pytest.mark.asyncio
    async def test_get_client_info_rate_limited_locally(self):
        client = MonobankClient()
        key = client._token_key("token")
        client._last_request_time[key] = time.time()

        with pytest.raises(RateLimitError):
            await client.get_client_info("token")


class TestMonobankClientGetStatements:
    """Tests for MonobankClient.get_statements."""

    @pytest.mark.asyncio
    async def test_successful_get_statements(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_data = [
            {
                "id": "tx1",
                "time": 1700000000,
                "description": "Payment",
                "mcc": 5411,
                "hold": False,
                "amount": -5000,
                "operationAmount": -5000,
                "currencyCode": 980,
                "commissionRate": 0,
                "cashbackAmount": 0,
                "balance": 95000,
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.get_statements("token", "acc1", 1000, 2000)

        assert len(result) == 1
        assert isinstance(result[0], MonobankStatementItem)
        assert result[0].id == "tx1"

    @pytest.mark.asyncio
    async def test_get_statements_429_raises_rate_limit(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            with pytest.raises(RateLimitError):
                await client.get_statements("token", "acc1", 1000, 2000)

    @pytest.mark.asyncio
    async def test_get_statements_request_error(self):
        client = MonobankClient()
        client._last_request_time.clear()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("timeout")
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            with pytest.raises(MonobankApiError, match="Failed to connect"):
                await client.get_statements("token", "acc1", 1000, 2000)

    @pytest.mark.asyncio
    async def test_get_statements_empty_list(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.get_statements("token", "acc1", 1000, 2000)

        assert result == []


class TestMonobankClientSetWebhook:
    """Tests for MonobankClient.set_webhook."""

    @pytest.mark.asyncio
    async def test_set_webhook_success(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.set_webhook("token", "https://example.com/webhook")

        assert result is True

    @pytest.mark.asyncio
    async def test_set_webhook_failure_returns_false(self):
        client = MonobankClient()
        client._last_request_time.clear()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = Exception("Connection error")
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.set_webhook("token", "https://example.com/webhook")

        assert result is False

    @pytest.mark.asyncio
    async def test_set_webhook_non_200_returns_false(self):
        client = MonobankClient()
        client._last_request_time.clear()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client_instance

            result = await client.set_webhook("token", "https://example.com/webhook")

        assert result is False


class TestMonobankClientWaitForRateLimit:
    """Tests for MonobankClient.wait_for_rate_limit."""

    @pytest.mark.asyncio
    async def test_wait_for_rate_limit_no_prior_request(self):
        client = MonobankClient()
        client._last_request_time.clear()

        # Should complete immediately without sleeping
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await client.wait_for_rate_limit("token")
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_wait_for_rate_limit_sleeps_when_needed(self):
        client = MonobankClient()
        key = client._token_key("token")
        client._last_request_time[key] = time.time()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await client.wait_for_rate_limit("token")
            mock_sleep.assert_called_once()
            # Sleep time should be around rate_limit_seconds
            sleep_time = mock_sleep.call_args[0][0]
            assert sleep_time > 0
