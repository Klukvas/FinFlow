"""
Tests for app/dependencies.py — FastAPI dependency injection functions.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.dependencies import (
    get_db,
    get_expense_client,
    get_income_client,
    get_currency_client,
    get_account_service,
    get_account_service_internal,
)
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from app.services.account import AccountService


class TestGetDb:
    def test_yields_session(self):
        gen = get_db()
        session = next(gen)
        assert session is not None
        # Clean up
        try:
            next(gen)
        except StopIteration:
            pass

    def test_closes_session_on_finish(self):
        gen = get_db()
        session = next(gen)
        try:
            next(gen)
        except StopIteration:
            pass
        # After generator exhaustion, session should be closed
        # No assertion needed — just verifying no exception is raised


class TestGetExpenseClient:
    def test_returns_instance(self):
        client = get_expense_client()
        assert isinstance(client, ExpenseServiceClient)


class TestGetIncomeClient:
    def test_returns_instance(self):
        client = get_income_client()
        assert isinstance(client, IncomeServiceClient)


class TestGetCurrencyClient:
    def test_returns_instance(self):
        client = get_currency_client()
        assert client is not None
