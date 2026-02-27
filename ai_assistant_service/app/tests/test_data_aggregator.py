"""Tests for data aggregator service."""

import hashlib
import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.services.data_aggregator import aggregate_data, _format_data
from app.schemas.prompts import PromptId
from app.exceptions import InsufficientDataError


TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


class TestAggregateData:
    async def test_successful_aggregation(self, sample_expense_data, sample_category_data):
        async def mock_fetch(source, user_id, workspace_id):
            if source == "expenses":
                return sample_expense_data
            if source == "categories":
                return sample_category_data
            if source == "accounts":
                return {"items": [{"name": "Checking", "balance": 5000}]}
            if source == "recurring":
                return {"items": [{"amount": 100, "schedule": "monthly"}]}
            return {"items": []}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            formatted, data_hash = await aggregate_data(
                PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert "EXPENSES" in formatted
        assert "CATEGORIES" in formatted
        assert len(data_hash) == 64  # Full SHA-256 hex digest

    async def test_hash_is_deterministic(self, sample_expense_data, sample_category_data):
        async def mock_fetch(source, user_id, workspace_id):
            if source == "expenses":
                return sample_expense_data
            if source == "categories":
                return sample_category_data
            return {"items": [{"name": "test"}]}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            _, hash1 = await aggregate_data(
                PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
            )
            _, hash2 = await aggregate_data(
                PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert hash1 == hash2

    async def test_insufficient_data_raises_error(self):
        async def mock_fetch(source, user_id, workspace_id):
            if source == "expenses":
                return {"items": [{"amount": 100}]}  # Only 1, need 5
            return {"items": []}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            with pytest.raises(InsufficientDataError):
                await aggregate_data(
                    PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
                )

    async def test_failed_required_source_raises_error(self):
        async def mock_fetch(source, user_id, workspace_id):
            if source == "expenses":
                return None  # Failed to fetch
            return {"items": []}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            with pytest.raises(InsufficientDataError):
                await aggregate_data(
                    PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
                )

    async def test_exception_in_fetch_treated_as_none(self, sample_expense_data):
        call_count = 0

        async def mock_fetch(source, user_id, workspace_id):
            nonlocal call_count
            call_count += 1
            if source == "expenses":
                return sample_expense_data
            if source == "categories":
                raise Exception("Network error")
            return {"items": [{"test": True}]}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            # categories fetch fails but it's not in thresholds for this prompt
            formatted, _ = await aggregate_data(
                PromptId.EXPENSES_REDUCE_SPENDING, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert "EXPENSES" in formatted

    async def test_debts_prompt_needs_debts(self, sample_debt_data, sample_income_data, sample_expense_data):
        async def mock_fetch(source, user_id, workspace_id):
            if source == "debts":
                return sample_debt_data
            if source == "incomes":
                return sample_income_data
            if source == "expenses":
                return sample_expense_data
            return {"items": []}

        with patch("app.services.data_aggregator.fetch_data", side_effect=mock_fetch):
            formatted, _ = await aggregate_data(
                PromptId.DEBTS_PAY_FIRST, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert "DEBTS" in formatted
        assert "Credit Card" in formatted


class TestFormatData:
    def test_formats_multiple_sources(self):
        data = {
            "expenses": {"items": [{"amount": 100, "category": "Food"}]},
            "incomes": {"items": [{"amount": 5000}]},
        }
        result = _format_data(data)
        assert "=== EXPENSES (1 records) ===" in result
        assert "=== INCOMES (1 records) ===" in result
        assert "100" in result

    def test_skips_none_sources(self):
        data = {
            "expenses": {"items": [{"amount": 100}]},
            "incomes": None,
        }
        result = _format_data(data)
        assert "EXPENSES" in result
        assert "INCOMES" not in result

    def test_skips_empty_items(self):
        data = {
            "expenses": {"items": [{"amount": 100}]},
            "accounts": {"items": []},
        }
        result = _format_data(data)
        assert "EXPENSES" in result
        assert "ACCOUNTS" not in result

    def test_hash_changes_with_different_data(self):
        data1 = {"expenses": {"items": [{"amount": 100}]}}
        data2 = {"expenses": {"items": [{"amount": 200}]}}
        formatted1 = _format_data(data1)
        formatted2 = _format_data(data2)
        hash1 = hashlib.sha256(formatted1.encode()).hexdigest()[:16]
        hash2 = hashlib.sha256(formatted2.encode()).hexdigest()[:16]
        assert hash1 != hash2

    def test_empty_aggregated_data(self):
        result = _format_data({})
        assert result == ""
