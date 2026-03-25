"""Tests for app/services/transaction_mapper.py - TransactionMapper."""

import pytest
from decimal import Decimal

from app.services.transaction_mapper import TransactionMapper
from app.schemas.monobank import MonobankStatementItem


def _make_statement_item(**overrides) -> MonobankStatementItem:
    """Helper to build a MonobankStatementItem with sensible defaults."""
    defaults = {
        "id": "tx_abc123",
        "time": 1700000000,
        "description": "ATB Market",
        "mcc": 5411,
        "hold": False,
        "amount": -5000,
        "operationAmount": -5000,
        "currencyCode": 980,
        "commissionRate": 0,
        "cashbackAmount": 0,
        "balance": 100000,
    }
    defaults.update(overrides)
    return MonobankStatementItem(**defaults)


class TestTransactionMapper:
    """Tests for the TransactionMapper.map_to_finflow static method."""

    def setup_method(self):
        self.mapper = TransactionMapper()

    def test_expense_negative_amount(self):
        item = _make_statement_item(amount=-5000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=10)

        assert result is not None
        assert result["type"] == "expense"
        assert result["external_id"] == "tx_abc123"
        assert result["mcc"] == 5411
        assert Decimal(result["data"]["amount"]) == Decimal("50.00")
        assert result["data"]["currency"] == "UAH"
        assert result["data"]["account_id"] == 10

    def test_income_positive_amount(self):
        item = _make_statement_item(amount=15000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=5)

        assert result is not None
        assert result["type"] == "income"
        assert Decimal(result["data"]["amount"]) == Decimal("150.00")

    def test_hold_transaction_returns_none(self):
        item = _make_statement_item(hold=True)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is None

    def test_description_includes_comment_when_present(self):
        item = _make_statement_item(
            description="Silpo", comment="groceries for the week"
        )
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert "Silpo" in result["data"]["description"]
        assert "groceries for the week" in result["data"]["description"]

    def test_description_without_comment(self):
        item = _make_statement_item(description="Rozetka", comment=None)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["data"]["description"] == "Rozetka"

    def test_currency_usd(self):
        item = _make_statement_item(currencyCode=840, amount=-1000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["data"]["currency"] == "USD"

    def test_currency_eur(self):
        item = _make_statement_item(currencyCode=978, amount=-2000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["data"]["currency"] == "EUR"

    def test_unknown_currency_code_uses_numeric_string(self):
        item = _make_statement_item(currencyCode=9999, amount=-100)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["data"]["currency"] == "9999"

    def test_category_id_set_when_provided(self):
        item = _make_statement_item(amount=-1000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1, category_id=42)

        assert result is not None
        assert result["data"]["category_id"] == 42

    def test_category_id_absent_when_none(self):
        item = _make_statement_item(amount=-1000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1, category_id=None)

        assert result is not None
        assert "category_id" not in result["data"]

    def test_date_formatted_as_iso_string(self):
        # 2023-11-14 in UTC
        item = _make_statement_item(time=1700000000)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        date_str = result["data"]["date"]
        assert len(date_str) == 10  # YYYY-MM-DD format
        assert "-" in date_str

    def test_amount_is_absolute_value(self):
        item = _make_statement_item(amount=-12345)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert Decimal(result["data"]["amount"]) == Decimal("123.45")

    def test_zero_amount_maps_to_income(self):
        """Zero amount is not negative, so it maps to income."""
        item = _make_statement_item(amount=0)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["type"] == "income"
        assert Decimal(result["data"]["amount"]) == Decimal("0.00")

    def test_small_amount_one_kopek(self):
        item = _make_statement_item(amount=-1)
        result = self.mapper.map_to_finflow(item, finflow_account_id=1)

        assert result is not None
        assert result["data"]["amount"] == "0.01"

    def test_finflow_account_id_passed_through(self):
        item = _make_statement_item(amount=-100)
        result = self.mapper.map_to_finflow(item, finflow_account_id=999)

        assert result is not None
        assert result["data"]["account_id"] == 999
