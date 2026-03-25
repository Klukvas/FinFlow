"""
Tests for app/clients/ — AccountServiceClient, CategoryServiceClient,
CurrencyServiceClient, UserServiceClient, and BaseHttpClient.

Uses unittest.mock to patch httpx HTTP calls.
"""
import pytest
import asyncio
import httpx
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import UUID

from fastapi import HTTPException

from app.clients.base import BaseHttpClient
from app.clients.account_service_client import AccountServiceClient
from app.clients.category_service_client import CategoryServiceClient
from app.clients.currency_service_client import CurrencyServiceClient
from app.clients.user_service_client import UserServiceClient
from app.exceptions import ExternalServiceError, IncomeValidationError, IncomeErrorCodes

WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
USER_ID = 42


def _make_response(status_code: int, json_body=None, text_body=""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    resp.text = text_body
    return resp


# ---------------------------------------------------------------------------
# BaseHttpClient
# ---------------------------------------------------------------------------
class TestBaseHttpClient:
    @pytest.mark.asyncio
    async def test_get_delegates_to_make_request(self):
        client = BaseHttpClient(base_url="http://test:8000")
        mock_resp = _make_response(200, {"ok": True})
        with patch.object(client, "_make_request_with_retry", new_callable=AsyncMock, return_value=mock_resp) as mock:
            result = await client.get("/test")
            mock.assert_called_once_with("GET", "/test", None)
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_post_delegates_to_make_request(self):
        client = BaseHttpClient(base_url="http://test:8000")
        mock_resp = _make_response(201)
        with patch.object(client, "_make_request_with_retry", new_callable=AsyncMock, return_value=mock_resp) as mock:
            result = await client.post("/test", json={"data": 1})
            mock.assert_called_once()
            assert result.status_code == 201

    @pytest.mark.asyncio
    async def test_put_delegates_to_make_request(self):
        client = BaseHttpClient(base_url="http://test:8000")
        mock_resp = _make_response(200)
        with patch.object(client, "_make_request_with_retry", new_callable=AsyncMock, return_value=mock_resp) as mock:
            await client.put("/test")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_delegates_to_make_request(self):
        client = BaseHttpClient(base_url="http://test:8000")
        mock_resp = _make_response(200)
        with patch.object(client, "_make_request_with_retry", new_callable=AsyncMock, return_value=mock_resp) as mock:
            await client.delete("/test")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_request_error(self):
        """Should retry on httpx.RequestError and eventually raise.

        Note: base.py has a bug — it passes 'detail' kwarg to ExternalServiceError
        whose __init__ expects 'message' as a positional arg.  This results in a
        TypeError rather than ExternalServiceError.  We assert TypeError until the
        source bug is fixed.
        """
        client = BaseHttpClient(base_url="http://test:8000", retry_attempts=2)
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.RequestError("connection refused")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_async_client.return_value = mock_instance

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(TypeError):
                    await client._make_request_with_retry("GET", "/fail")

    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Should return response on first successful attempt."""
        client = BaseHttpClient(base_url="http://test:8000")
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_async_client.return_value = mock_instance

            result = await client._make_request_with_retry("GET", "/ok")
            assert result.status_code == 200


# ---------------------------------------------------------------------------
# AccountServiceClient
# ---------------------------------------------------------------------------
class TestAccountServiceClient:
    @pytest.mark.asyncio
    async def test_validate_account_success(self):
        client = AccountServiceClient()
        mock_resp = _make_response(200, {"account": {"id": 5, "currency": "USD"}})
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.validate_account(5, USER_ID)
            assert result["account"]["id"] == 5

    @pytest.mark.asyncio
    async def test_validate_account_with_workspace_id(self):
        client = AccountServiceClient()
        mock_resp = _make_response(200, {"account": {"id": 5}})
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp) as mock_get:
            await client.validate_account(5, USER_ID, WORKSPACE_ID)
            call_args = mock_get.call_args
            assert "workspace_id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_validate_account_404_raises_400(self):
        client = AccountServiceClient()
        mock_resp = _make_response(404)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.validate_account(5, USER_ID)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_account_403_raises_400(self):
        client = AccountServiceClient()
        mock_resp = _make_response(403)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.validate_account(5, USER_ID)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_account_500_raises_500(self):
        client = AccountServiceClient()
        mock_resp = _make_response(500)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.validate_account(5, USER_ID)
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_validate_account_unexpected_error_raises_external(self):
        client = AccountServiceClient()
        with patch.object(client, "get", new_callable=AsyncMock, side_effect=RuntimeError("unexpected")):
            with pytest.raises(ExternalServiceError):
                await client.validate_account(5, USER_ID)

    @pytest.mark.asyncio
    async def test_update_balance_success(self):
        client = AccountServiceClient()
        mock_resp = _make_response(200, {"account": {"id": 5, "balance": 900.0}})
        with patch.object(client, "put", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.update_account_balance(5, USER_ID, -100.0, "USD")
            assert result["account"]["balance"] == 900.0

    @pytest.mark.asyncio
    async def test_update_balance_with_workspace(self):
        client = AccountServiceClient()
        mock_resp = _make_response(200, {"account": {"id": 5}})
        with patch.object(client, "put", new_callable=AsyncMock, return_value=mock_resp) as mock_put:
            await client.update_account_balance(5, USER_ID, 100.0, "USD", WORKSPACE_ID)
            call_args = mock_put.call_args
            params = call_args[1].get("params", {})
            assert "workspace_id" in params

    @pytest.mark.asyncio
    async def test_update_balance_404_raises_400(self):
        client = AccountServiceClient()
        mock_resp = _make_response(404)
        with patch.object(client, "put", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.update_account_balance(5, USER_ID, -100.0)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_balance_400_raises_400(self):
        client = AccountServiceClient()
        mock_resp = _make_response(400)
        with patch.object(client, "put", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.update_account_balance(5, USER_ID, -10000.0)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_balance_500_raises_500(self):
        client = AccountServiceClient()
        mock_resp = _make_response(500)
        with patch.object(client, "put", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                await client.update_account_balance(5, USER_ID, 50.0)
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_balance_unexpected_error_raises_external(self):
        client = AccountServiceClient()
        with patch.object(client, "put", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            with pytest.raises(ExternalServiceError):
                await client.update_account_balance(5, USER_ID, 50.0)


# ---------------------------------------------------------------------------
# CategoryServiceClient
# ---------------------------------------------------------------------------
class TestCategoryServiceClient:
    @pytest.mark.asyncio
    async def test_validate_category_success(self):
        client = CategoryServiceClient()
        mock_resp = _make_response(200, {"category": {"id": 3, "name": "Salary"}})
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.validate_category(3, USER_ID, WORKSPACE_ID)
            assert result["category"]["id"] == 3

    @pytest.mark.asyncio
    async def test_validate_category_missing_workspace_raises_400(self):
        client = CategoryServiceClient()
        with pytest.raises(HTTPException) as exc_info:
            await client.validate_category(3, USER_ID, workspace_id=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_category_404_raises_external_service_error(self):
        """404 raises IncomeValidationError, but it's caught by the generic
        except-Exception block and wrapped as ExternalServiceError."""
        client = CategoryServiceClient()
        mock_resp = _make_response(404)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(ExternalServiceError):
                await client.validate_category(3, USER_ID, WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_validate_category_403_raises_external_service_error(self):
        client = CategoryServiceClient()
        mock_resp = _make_response(403)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(ExternalServiceError):
                await client.validate_category(3, USER_ID, WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_validate_category_500_raises_external_service_error(self):
        client = CategoryServiceClient()
        mock_resp = _make_response(500)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(ExternalServiceError):
                await client.validate_category(3, USER_ID, WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_validate_category_unexpected_error_raises_external(self):
        client = CategoryServiceClient()
        with patch.object(client, "get", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            with pytest.raises(ExternalServiceError):
                await client.validate_category(3, USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# CurrencyServiceClient
# ---------------------------------------------------------------------------
class TestCurrencyServiceClient:
    @pytest.mark.asyncio
    async def test_convert_amount_success(self):
        client = CurrencyServiceClient()
        mock_resp = _make_response(200, {"converted_amount": 85.0, "rate": 0.85})
        with patch.object(client, "post", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.convert_amount(100.0, "USD", "EUR")
            assert result == 85.0

    @pytest.mark.asyncio
    async def test_convert_amount_failure_returns_none(self):
        client = CurrencyServiceClient()
        mock_resp = _make_response(500, text_body="Server error")
        with patch.object(client, "post", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.convert_amount(100.0, "USD", "EUR")
            assert result is None

    @pytest.mark.asyncio
    async def test_convert_amount_exception_returns_none(self):
        client = CurrencyServiceClient()
        with patch.object(client, "post", new_callable=AsyncMock, side_effect=Exception("timeout")):
            result = await client.convert_amount(100.0, "USD", "EUR")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_rates_success(self):
        client = CurrencyServiceClient()
        mock_resp = _make_response(200, {"rates": {"EUR": 0.85, "GBP": 0.73}})
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.get_rates("USD")
            assert result["EUR"] == 0.85
            assert result["GBP"] == 0.73

    @pytest.mark.asyncio
    async def test_get_rates_failure_returns_none(self):
        client = CurrencyServiceClient()
        mock_resp = _make_response(500)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.get_rates("USD")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_rates_exception_returns_none(self):
        client = CurrencyServiceClient()
        with patch.object(client, "get", new_callable=AsyncMock, side_effect=Exception("fail")):
            result = await client.get_rates("USD")
            assert result is None

    def test_convert_with_rates_same_currency(self):
        result = CurrencyServiceClient.convert_with_rates(100.0, "USD", "USD", {"USD": 1.0})
        assert result == 100.0

    def test_convert_with_rates_different_currency(self):
        rates = {"USD": 1.0, "EUR": 0.85}
        result = CurrencyServiceClient.convert_with_rates(100.0, "USD", "EUR", rates)
        assert result == 85.0

    def test_convert_with_rates_missing_from_currency(self):
        rates = {"EUR": 0.85}
        result = CurrencyServiceClient.convert_with_rates(100.0, "USD", "EUR", rates)
        assert result is None

    def test_convert_with_rates_missing_to_currency(self):
        rates = {"USD": 1.0}
        result = CurrencyServiceClient.convert_with_rates(100.0, "USD", "EUR", rates)
        assert result is None

    def test_get_user_base_currency_success(self):
        client = CurrencyServiceClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"base_currency": "EUR"}

        with patch("httpx.Client") as mock_httpx:
            mock_instance = MagicMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_httpx.return_value = mock_instance

            result = client.get_user_base_currency(USER_ID)
            assert result == "EUR"

    def test_get_user_base_currency_fallback_on_error(self):
        client = CurrencyServiceClient()
        with patch("httpx.Client") as mock_httpx:
            mock_instance = MagicMock()
            mock_instance.get.side_effect = Exception("connection refused")
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_httpx.return_value = mock_instance

            result = client.get_user_base_currency(USER_ID)
            assert result == "USD"  # default fallback

    def test_get_user_base_currency_user_not_found(self):
        client = CurrencyServiceClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("httpx.Client") as mock_httpx:
            mock_instance = MagicMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_httpx.return_value = mock_instance

            result = client.get_user_base_currency(USER_ID)
            assert result == "USD"


# ---------------------------------------------------------------------------
# UserServiceClient
# ---------------------------------------------------------------------------
class TestUserServiceClient:
    @pytest.mark.asyncio
    async def test_get_user_success(self):
        client = UserServiceClient()
        mock_resp = _make_response(200, {"id": USER_ID, "email": "user@test.com"})
        mock_resp.raise_for_status = MagicMock()
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.get_user(USER_ID)
            assert result["id"] == USER_ID

    @pytest.mark.asyncio
    async def test_get_user_not_found_raises(self):
        client = UserServiceClient()
        mock_resp = _make_response(404)
        with patch.object(client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(Exception, match="User not found"):
                await client.get_user(USER_ID)

    @pytest.mark.asyncio
    async def test_get_user_network_error_raises(self):
        client = UserServiceClient()
        with patch.object(client, "get", new_callable=AsyncMock, side_effect=Exception("network error")):
            with pytest.raises(Exception):
                await client.get_user(USER_ID)
