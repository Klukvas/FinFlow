"""Tests for app/clients/ - Service client classes."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from app.clients.base import BaseServiceClient
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.clients.account_client import AccountServiceClient
from app.exceptions import TransactionLimitExceededError


class TestBaseServiceClient:
    """Tests for BaseServiceClient."""

    def test_base_url_trailing_slash_stripped(self):
        client = BaseServiceClient("http://example.com/")
        assert client.base_url == "http://example.com"

    def test_base_url_without_trailing_slash(self):
        client = BaseServiceClient("http://example.com")
        assert client.base_url == "http://example.com"

    def test_timeout_default(self):
        client = BaseServiceClient("http://example.com")
        assert client.timeout == 30

    def test_timeout_custom(self):
        client = BaseServiceClient("http://example.com", timeout=60)
        assert client.timeout == 60

    @pytest.mark.asyncio
    async def test_get_method(self):
        client = BaseServiceClient("http://example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "value"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await client.get("/endpoint")

        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_post_method(self):
        client = BaseServiceClient("http://example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await client.post("/endpoint", data={"key": "val"})

        assert result == {"id": 1}

    @pytest.mark.asyncio
    async def test_put_method(self):
        client = BaseServiceClient("http://example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await client.put("/endpoint", data={"key": "val"})

        assert result == {"updated": True}

    @pytest.mark.asyncio
    async def test_delete_method(self):
        client = BaseServiceClient("http://example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {"deleted": True}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await client.delete("/endpoint")

        assert result == {"deleted": True}

    @pytest.mark.asyncio
    async def test_http_status_error_propagates(self):
        client = BaseServiceClient("http://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/endpoint")

    @pytest.mark.asyncio
    async def test_request_error_propagates(self):
        client = BaseServiceClient("http://example.com")

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.RequestError("Connection refused")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            with pytest.raises(httpx.RequestError):
                await client.get("/endpoint")


class TestExpenseServiceClient:
    """Tests for ExpenseServiceClient."""

    @pytest.mark.asyncio
    async def test_create_expense_success(self):
        client = ExpenseServiceClient()

        with patch.object(
            client, "post", new_callable=AsyncMock, return_value={"id": 1}
        ):
            result = await client.create_expense(
                {"amount": "50.00"}, user_id=1, workspace_id="ws-123"
            )

        assert result == {"id": 1}

    @pytest.mark.asyncio
    async def test_create_expense_429_raises_limit_error(self):
        client = ExpenseServiceClient()

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with patch.object(
            client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_response
            ),
        ):
            with pytest.raises(TransactionLimitExceededError) as exc_info:
                await client.create_expense(
                    {"amount": "50.00"}, user_id=1, workspace_id="ws-123"
                )

            assert exc_info.value.transaction_type == "expense"

    @pytest.mark.asyncio
    async def test_create_expense_non_429_error_propagates(self):
        client = ExpenseServiceClient()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(
            client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_response
            ),
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await client.create_expense(
                    {"amount": "50.00"}, user_id=1, workspace_id="ws-123"
                )


class TestIncomeServiceClient:
    """Tests for IncomeServiceClient."""

    @pytest.mark.asyncio
    async def test_create_income_success(self):
        client = IncomeServiceClient()

        with patch.object(
            client, "post", new_callable=AsyncMock, return_value={"id": 2}
        ):
            result = await client.create_income(
                {"amount": "100.00"}, user_id=1, workspace_id="ws-123"
            )

        assert result == {"id": 2}

    @pytest.mark.asyncio
    async def test_create_income_429_raises_limit_error(self):
        client = IncomeServiceClient()

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with patch.object(
            client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_response
            ),
        ):
            with pytest.raises(TransactionLimitExceededError) as exc_info:
                await client.create_income(
                    {"amount": "100.00"}, user_id=1, workspace_id="ws-123"
                )

            assert exc_info.value.transaction_type == "income"


class TestCategoryServiceClient:
    """Tests for CategoryServiceClient."""

    @pytest.mark.asyncio
    async def test_get_category_by_mcc_success(self):
        client = CategoryServiceClient()

        with patch.object(
            client,
            "get",
            new_callable=AsyncMock,
            return_value={"id": 10, "name": "Groceries"},
        ):
            result = await client.get_category_by_mcc(5411, user_id=1, workspace_id="ws-123")

        assert result == {"id": 10, "name": "Groceries"}

    @pytest.mark.asyncio
    async def test_get_category_by_mcc_not_found_returns_none(self):
        client = CategoryServiceClient()

        with patch.object(
            client,
            "get",
            new_callable=AsyncMock,
            side_effect=Exception("Not found"),
        ):
            result = await client.get_category_by_mcc(9999, user_id=1, workspace_id="ws-123")

        assert result is None


class TestAccountServiceClient:
    """Tests for AccountServiceClient."""

    @pytest.mark.asyncio
    async def test_get_account_success(self):
        client = AccountServiceClient()

        with patch.object(
            client,
            "get",
            new_callable=AsyncMock,
            return_value={"id": 1, "name": "Main Account"},
        ):
            result = await client.get_account(1, user_id=1, workspace_id="ws-123")

        assert result == {"id": 1, "name": "Main Account"}

    @pytest.mark.asyncio
    async def test_get_account_error_returns_none(self):
        client = AccountServiceClient()

        with patch.object(
            client,
            "get",
            new_callable=AsyncMock,
            side_effect=Exception("Connection error"),
        ):
            result = await client.get_account(999, user_id=1, workspace_id="ws-123")

        assert result is None
