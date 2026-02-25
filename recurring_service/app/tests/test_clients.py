"""Tests for expense and income client create methods"""
import pytest
from unittest.mock import AsyncMock, patch

from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient


class TestExpenseServiceClient:
    @pytest.mark.asyncio
    async def test_create_expense_sends_correct_params(self):
        """Verify create_expense passes user_id and workspace_id as query params"""
        client = ExpenseServiceClient()
        mock_response = {"id": "abc-123", "amount": 100.0}

        with patch.object(client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            result = await client.create_expense(
                {"amount": 100.0, "currency": "USD", "category_id": 1},
                user_id=42,
                workspace_id="ws-uuid-123"
            )

        mock_post.assert_called_once_with(
            "/internal/",
            data={"amount": 100.0, "currency": "USD", "category_id": 1},
            params={"user_id": 42, "workspace_id": "ws-uuid-123"}
        )
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_expense_endpoint_is_internal(self):
        """Verify the endpoint is /internal/ not /api/v1/expenses"""
        client = ExpenseServiceClient()

        with patch.object(client, "post", new_callable=AsyncMock, return_value={}) as mock_post:
            await client.create_expense({}, user_id=1, workspace_id="ws-1")

        endpoint = mock_post.call_args[0][0]
        assert endpoint == "/internal/"


class TestIncomeServiceClient:
    @pytest.mark.asyncio
    async def test_create_income_sends_correct_params(self):
        """Verify create_income passes user_id and workspace_id as query params"""
        client = IncomeServiceClient()
        mock_response = {"id": "inc-123", "amount": 200.0}

        with patch.object(client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            result = await client.create_income(
                {"amount": 200.0, "currency": "EUR", "category_id": 2},
                user_id=10,
                workspace_id="ws-uuid-456"
            )

        mock_post.assert_called_once_with(
            "/internal/",
            data={"amount": 200.0, "currency": "EUR", "category_id": 2},
            params={"user_id": 10, "workspace_id": "ws-uuid-456"}
        )
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_income_endpoint_is_internal(self):
        """Verify the endpoint is /internal/ not /api/v1/incomes"""
        client = IncomeServiceClient()

        with patch.object(client, "post", new_callable=AsyncMock, return_value={}) as mock_post:
            await client.create_income({}, user_id=1, workspace_id="ws-1")

        endpoint = mock_post.call_args[0][0]
        assert endpoint == "/internal/"
