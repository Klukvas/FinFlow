"""Tests for app/schemas/income.py — Pydantic model validation."""
import pytest
from datetime import datetime, date
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.schemas.income import (
    IncomeBase,
    IncomeCreate,
    IncomeUpdate,
    IncomeOut,
    IncomeSummary,
    IncomeStats,
    IncomeListResponse,
    CategoryIncomeStatistics,
    IncomesByCategoryResponse,
)


# ---------------------------------------------------------------------------
# IncomeBase / IncomeCreate
# ---------------------------------------------------------------------------
class TestIncomeCreate:
    def test_valid_minimal(self):
        """Only amount is required."""
        data = IncomeCreate(amount=100.0)
        assert data.amount == 100.0
        assert data.category_id is None
        assert data.account_id is None
        assert data.currency == "USD"
        assert data.description is None
        assert data.date is None

    def test_valid_full(self):
        data = IncomeCreate(
            amount=999.99,
            category_id=5,
            account_id=10,
            currency="EUR",
            description="Salary",
            date="2025-01-15",
        )
        assert data.amount == 999.99
        assert data.category_id == 5
        assert data.account_id == 10
        assert data.currency == "EUR"
        assert data.description == "Salary"
        assert data.date == "2025-01-15"

    def test_amount_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            IncomeCreate(amount=0)
        assert "amount" in str(exc_info.value).lower()

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=-50.0)

    def test_category_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=100.0, category_id=0)

    def test_account_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=100.0, account_id=0)

    def test_currency_max_length_3(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=100.0, currency="ABCD")

    def test_currency_min_length_3(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=100.0, currency="AB")

    def test_description_max_length_500(self):
        with pytest.raises(ValidationError):
            IncomeCreate(amount=100.0, description="x" * 501)

    def test_description_exactly_500_is_valid(self):
        data = IncomeCreate(amount=100.0, description="x" * 500)
        assert len(data.description) == 500


# ---------------------------------------------------------------------------
# IncomeUpdate
# ---------------------------------------------------------------------------
class TestIncomeUpdate:
    def test_all_fields_optional(self):
        data = IncomeUpdate()
        assert data.amount is None
        assert data.category_id is None
        assert data.account_id is None
        assert data.currency is None
        assert data.description is None
        assert data.date is None

    def test_partial_update_amount_only(self):
        data = IncomeUpdate(amount=200.0)
        assert data.amount == 200.0
        assert data.description is None

    def test_amount_must_be_positive_if_provided(self):
        with pytest.raises(ValidationError):
            IncomeUpdate(amount=0)

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            IncomeUpdate(amount=-10.0)

    def test_account_id_must_be_positive_if_provided(self):
        with pytest.raises(ValidationError):
            IncomeUpdate(account_id=0)

    def test_currency_length_validation(self):
        with pytest.raises(ValidationError):
            IncomeUpdate(currency="AB")

    def test_description_max_length(self):
        with pytest.raises(ValidationError):
            IncomeUpdate(description="x" * 501)


# ---------------------------------------------------------------------------
# IncomeOut
# ---------------------------------------------------------------------------
class TestIncomeOut:
    def test_from_attributes(self):
        """IncomeOut should work with from_attributes = True (ORM mode)."""

        class FakeIncome:
            def __init__(self):
                self.id = 1
                self.user_id = 42
                self.workspace_id = UUID("550e8400-e29b-41d4-a716-446655440000")
                self.amount = 100.0
                self.category_id = 5
                self.account_id = 10
                self.currency = "USD"
                self.description = "test"
                self.date = datetime(2025, 1, 15)
                self.created_at = datetime(2025, 1, 15, 10, 0)
                self.updated_at = datetime(2025, 1, 15, 10, 0)

        out = IncomeOut.model_validate(FakeIncome())
        assert out.id == 1
        assert out.user_id == 42
        assert out.amount == 100.0
        assert out.currency == "USD"

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            IncomeOut(amount=100.0)  # missing id, user_id, etc.


# ---------------------------------------------------------------------------
# IncomeSummary
# ---------------------------------------------------------------------------
class TestIncomeSummary:
    def test_valid_summary(self):
        s = IncomeSummary(
            total_income=5000.0,
            count=10,
            average_income=500.0,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        assert s.total_income == 5000.0
        assert s.count == 10
        assert s.average_income == 500.0

    def test_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            IncomeSummary(total_income=100.0)


# ---------------------------------------------------------------------------
# IncomeStats
# ---------------------------------------------------------------------------
class TestIncomeStats:
    def test_valid_stats(self):
        stats = IncomeStats(
            total_income=10000.0,
            monthly_income=2000.0,
            yearly_income=8000.0,
            income_count=20,
            average_income=500.0,
        )
        assert stats.total_income == 10000.0
        assert stats.income_count == 20


# ---------------------------------------------------------------------------
# IncomeListResponse
# ---------------------------------------------------------------------------
class TestIncomeListResponse:
    def test_valid_response(self):
        resp = IncomeListResponse(
            items=[],
            total=0,
            page=1,
            size=50,
            pages=0,
        )
        assert resp.total == 0
        assert resp.pages == 0
        assert resp.items == []

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            IncomeListResponse(items=[])


# ---------------------------------------------------------------------------
# CategoryIncomeStatistics
# ---------------------------------------------------------------------------
class TestCategoryIncomeStatistics:
    def test_valid_statistics(self):
        stats = CategoryIncomeStatistics(
            total_amount=1000.0,
            count=5,
            average_amount=200.0,
            currency="USD",
        )
        assert stats.total_amount == 1000.0
        assert stats.count == 5
        assert stats.currency == "USD"


# ---------------------------------------------------------------------------
# IncomesByCategoryResponse
# ---------------------------------------------------------------------------
class TestIncomesByCategoryResponse:
    def test_valid_response(self):
        stats = CategoryIncomeStatistics(
            total_amount=1000.0,
            count=0,
            average_amount=0.0,
            currency="USD",
        )
        resp = IncomesByCategoryResponse(incomes=[], statistics=stats)
        assert resp.incomes == []
        assert resp.statistics.total_amount == 1000.0
