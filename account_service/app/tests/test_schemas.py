"""
Tests for app/schemas/account.py — Pydantic schema validation.
"""
import pytest
from datetime import datetime
from uuid import UUID

from pydantic import ValidationError

from app.schemas.account import (
    AccountBase,
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountSummary,
    AccountTransaction,
    AccountTransactionSummary,
    AccountStatisticsResponse,
)
from app.models.account import AccountType


class TestAccountCreate:
    def test_valid_minimal(self):
        data = AccountCreate(name="Savings", type=AccountType.SAVINGS)
        assert data.name == "Savings"
        assert data.type == AccountType.SAVINGS
        assert data.currency == "USD"
        assert data.balance == 0.0
        assert data.description is None

    def test_valid_full(self):
        data = AccountCreate(
            name="Checking",
            type=AccountType.CHECKING,
            currency="EUR",
            balance=500.50,
            description="My checking account",
        )
        assert data.currency == "EUR"
        assert data.balance == 500.50

    def test_currency_uppercased(self):
        data = AccountCreate(name="Test", type=AccountType.CASH, currency="eur")
        assert data.currency == "EUR"

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="A" * 101, type=AccountType.CASH)

    def test_name_empty_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="", type=AccountType.CASH)

    def test_balance_exceeds_max(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", type=AccountType.CASH, balance=1000000000.0)

    def test_balance_below_min(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", type=AccountType.CASH, balance=-1000000000.0)

    def test_currency_too_short(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", type=AccountType.CASH, currency="US")

    def test_currency_too_long(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", type=AccountType.CASH, currency="USDD")

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", type="invalid_type")

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            AccountCreate(
                name="Test",
                type=AccountType.CASH,
                description="A" * 501,
            )

    def test_all_account_types_accepted(self):
        for account_type in AccountType:
            data = AccountCreate(name="Test", type=account_type)
            assert data.type == account_type


class TestAccountUpdate:
    def test_all_none(self):
        data = AccountUpdate()
        assert data.name is None
        assert data.type is None
        assert data.currency is None
        assert data.balance is None
        assert data.description is None
        assert data.is_active is None

    def test_partial_update(self):
        data = AccountUpdate(name="New Name", balance=500.0)
        assert data.name == "New Name"
        assert data.balance == 500.0
        assert data.type is None

    def test_currency_uppercased(self):
        data = AccountUpdate(currency="gbp")
        assert data.currency == "GBP"

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            AccountUpdate(name="A" * 101)

    def test_balance_exceeds_max(self):
        with pytest.raises(ValidationError):
            AccountUpdate(balance=1000000000.0)

    def test_is_active_toggle(self):
        data = AccountUpdate(is_active=False)
        assert data.is_active is False


class TestAccountResponse:
    def test_from_attributes(self):
        """AccountResponse should support from_attributes mode."""
        assert AccountResponse.model_config.get("from_attributes") is True

    def test_valid_response(self):
        now = datetime.utcnow()
        resp = AccountResponse(
            id=1,
            name="Test",
            type=AccountType.SAVINGS,
            currency="USD",
            balance=100.0,
            owner_id=1,
            workspace_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            is_active=True,
            is_archived=False,
            is_read_only=False,
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.is_read_only is False


class TestAccountSummary:
    def test_defaults(self):
        summary = AccountSummary(
            id=1,
            name="Test",
            type=AccountType.CASH,
            currency="USD",
            balance=500.0,
            is_active=True,
        )
        assert summary.transaction_count == 0
        assert summary.last_transaction_date is None


class TestAccountTransaction:
    def test_creation(self):
        now = datetime.utcnow()
        txn = AccountTransaction(
            id=1,
            amount=50.0,
            description="Groceries",
            date=now,
            type="expense",
            category_id=10,
            category_name="Food",
        )
        assert txn.type == "expense"
        assert txn.amount == 50.0

    def test_optional_fields(self):
        now = datetime.utcnow()
        txn = AccountTransaction(
            id=1, amount=100.0, description=None, date=now, type="income"
        )
        assert txn.category_id is None
        assert txn.category_name is None


class TestAccountTransactionSummary:
    def test_defaults(self):
        summary = AccountTransactionSummary(
            account=AccountSummary(
                id=1,
                name="Test",
                type=AccountType.CASH,
                currency="USD",
                balance=500.0,
                is_active=True,
            ),
            transactions=[],
        )
        assert summary.total_income == 0.0
        assert summary.total_expenses == 0.0
        assert summary.net_change == 0.0


class TestAccountStatisticsResponse:
    def test_creation(self):
        stats = AccountStatisticsResponse(
            total_accounts=5,
            active_accounts=3,
            total_balance=15000.50,
            currency="USD",
            unconvertible_accounts_count=1,
        )
        assert stats.total_accounts == 5
        assert stats.unconvertible_accounts_count == 1
