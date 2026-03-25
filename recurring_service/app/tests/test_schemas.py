"""Tests for all Pydantic schemas."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from app.schemas.recurring_payment import (
    RecurringPaymentBase,
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    RecurringPaymentResponse,
    RecurringPaymentListResponse,
    RecurringPaymentStatusUpdate,
)
from app.schemas.payment_schedule import (
    PaymentScheduleResponse,
    PaymentScheduleListResponse,
)


class TestRecurringPaymentCreate:
    def test_valid_monthly_payment(self):
        data = RecurringPaymentCreate(
            name="Monthly Rent",
            amount=Decimal("1500.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 1},
            start_date=date(2025, 1, 1),
        )
        assert data.name == "Monthly Rent"
        assert data.amount == Decimal("1500.00")
        assert data.schedule_type == "monthly"

    def test_valid_weekly_payment(self):
        data = RecurringPaymentCreate(
            name="Weekly Groceries",
            amount=Decimal("200.00"),
            currency="USD",
            category_id=2,
            payment_type="EXPENSE",
            schedule_type="weekly",
            schedule_config={"day_of_week": 1},
            start_date=date(2025, 1, 6),
        )
        assert data.schedule_config["day_of_week"] == 1

    def test_valid_daily_payment(self):
        data = RecurringPaymentCreate(
            name="Daily Coffee",
            amount=Decimal("5.00"),
            currency="USD",
            category_id=3,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        assert data.schedule_config == {}

    def test_valid_yearly_payment(self):
        data = RecurringPaymentCreate(
            name="Annual Insurance",
            amount=Decimal("5000.00"),
            currency="USD",
            category_id=4,
            payment_type="EXPENSE",
            schedule_type="yearly",
            schedule_config={"month": 6, "day": 15},
            start_date=date(2025, 1, 1),
        )
        assert data.schedule_config["month"] == 6

    def test_valid_income_payment(self):
        data = RecurringPaymentCreate(
            name="Monthly Salary",
            amount=Decimal("5000.00"),
            currency="USD",
            category_id=5,
            payment_type="INCOME",
            schedule_type="monthly",
            schedule_config={"day_of_month": 25},
            start_date=date(2025, 1, 1),
        )
        assert data.payment_type == "INCOME"

    def test_rejects_empty_name(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
            )

    def test_rejects_negative_amount(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("-100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
            )

    def test_rejects_zero_amount(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("0"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
            )

    def test_rejects_invalid_payment_type(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="TRANSFER",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
            )

    def test_rejects_invalid_schedule_type(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="biweekly",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )

    def test_rejects_invalid_currency_length(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="US",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
            )

    def test_end_date_must_be_after_start_date(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 6, 1),
                end_date=date(2025, 1, 1),
            )

    def test_end_date_equal_to_start_date_rejected(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 1},
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 1),
            )

    def test_valid_end_date_after_start(self):
        data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 1},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        assert data.end_date == date(2025, 12, 31)

    def test_daily_rejects_nonempty_config(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="daily",
                schedule_config={"day_of_week": 1},
                start_date=date(2025, 1, 1),
            )

    def test_weekly_requires_day_of_week(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="weekly",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )

    def test_weekly_rejects_invalid_day_of_week(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="weekly",
                schedule_config={"day_of_week": 7},
                start_date=date(2025, 1, 1),
            )

    def test_monthly_requires_day_of_month(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )

    def test_monthly_rejects_invalid_day_of_month(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="monthly",
                schedule_config={"day_of_month": 32},
                start_date=date(2025, 1, 1),
            )

    def test_yearly_requires_month_and_day(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="yearly",
                schedule_config={"month": 6},
                start_date=date(2025, 1, 1),
            )

    def test_yearly_rejects_invalid_month(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentCreate(
                name="Test",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="yearly",
                schedule_config={"month": 13, "day": 1},
                start_date=date(2025, 1, 1),
            )


class TestRecurringPaymentUpdate:
    def test_all_fields_optional(self):
        data = RecurringPaymentUpdate()
        assert data.name is None
        assert data.amount is None
        assert data.status is None

    def test_partial_update(self):
        data = RecurringPaymentUpdate(name="New Name", amount=Decimal("200.00"))
        assert data.name == "New Name"
        assert data.amount == Decimal("200.00")
        assert data.currency is None

    def test_status_update_valid(self):
        data = RecurringPaymentUpdate(status="paused")
        assert data.status == "paused"

    def test_status_update_invalid(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentUpdate(status="invalid_status")

    def test_rejects_negative_amount(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentUpdate(amount=Decimal("-50.00"))


class TestRecurringPaymentResponse:
    def test_from_attributes_enabled(self):
        assert RecurringPaymentResponse.model_config.get("from_attributes") is True

    def test_valid_response(self):
        payment_id = uuid4()
        workspace_id = uuid4()
        response = RecurringPaymentResponse(
            id=payment_id,
            user_id=1,
            workspace_id=workspace_id,
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 1},
            start_date=date(2025, 1, 1),
            end_date=None,
            status="active",
            last_executed=None,
            next_execution=date(2025, 1, 1),
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
            is_read_only=False,
        )
        assert response.id == payment_id
        assert response.is_read_only is False


class TestRecurringPaymentListResponse:
    def test_valid_list_response(self):
        response = RecurringPaymentListResponse(
            items=[],
            total=0,
            page=1,
            size=50,
            pages=0,
        )
        assert response.total == 0
        assert response.pages == 0


class TestRecurringPaymentStatusUpdate:
    def test_valid_statuses(self):
        for status in ["active", "paused", "completed", "cancelled"]:
            update = RecurringPaymentStatusUpdate(status=status)
            assert update.status == status

    def test_invalid_status(self):
        with pytest.raises(PydanticValidationError):
            RecurringPaymentStatusUpdate(status="deleted")


class TestPaymentScheduleResponse:
    def test_from_attributes_enabled(self):
        assert PaymentScheduleResponse.model_config.get("from_attributes") is True

    def test_valid_schedule_response(self):
        schedule_id = uuid4()
        payment_id = uuid4()
        response = PaymentScheduleResponse(
            id=schedule_id,
            recurring_payment_id=payment_id,
            execution_date=date(2025, 1, 15),
            status="executed",
            created_expense_id=101,
            created_income_id=None,
            error_message=None,
            executed_at=datetime(2025, 1, 15, 0, 1, 0),
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 15),
        )
        assert response.id == schedule_id
        assert response.status == "executed"
        assert response.created_expense_id == 101


class TestPaymentScheduleListResponse:
    def test_valid_list_response(self):
        response = PaymentScheduleListResponse(
            items=[],
            total=0,
            page=1,
            size=50,
            pages=0,
        )
        assert response.total == 0
        assert response.pages == 0
