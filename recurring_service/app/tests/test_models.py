"""Tests for SQLAlchemy models."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.models.recurring_payment import RecurringPayment
from app.models.payment_schedule import PaymentSchedule


class TestRecurringPaymentModel:
    def test_repr(self):
        payment = RecurringPayment()
        payment.id = uuid4()
        payment.name = "Test Payment"
        payment.payment_type = "EXPENSE"
        repr_str = repr(payment)
        assert "Test Payment" in repr_str
        assert "EXPENSE" in repr_str

    def test_to_dict(self):
        payment_id = uuid4()
        payment = RecurringPayment()
        payment.id = payment_id
        payment.user_id = 1
        payment.name = "Monthly Rent"
        payment.description = "Rent payment"
        payment.amount = Decimal("1500.00")
        payment.currency = "USD"
        payment.category_id = 1
        payment.payment_type = "EXPENSE"
        payment.schedule_type = "monthly"
        payment.schedule_config = {"day_of_month": 1}
        payment.start_date = date(2025, 1, 1)
        payment.end_date = None
        payment.status = "active"
        payment.last_executed = None
        payment.next_execution = date(2025, 1, 1)
        payment.created_at = datetime(2025, 1, 1, 0, 0, 0)
        payment.updated_at = datetime(2025, 1, 1, 0, 0, 0)

        result = payment.to_dict()
        assert result["id"] == str(payment_id)
        assert result["user_id"] == "1"
        assert result["name"] == "Monthly Rent"
        assert result["amount"] == 1500.0
        assert result["currency"] == "USD"
        assert result["payment_type"] == "EXPENSE"
        assert result["schedule_type"] == "monthly"
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] is None
        assert result["status"] == "active"
        assert result["last_executed"] is None
        assert result["next_execution"] == "2025-01-01"

    def test_to_dict_with_last_executed(self):
        payment = RecurringPayment()
        payment.id = uuid4()
        payment.user_id = 1
        payment.name = "Test"
        payment.description = None
        payment.amount = Decimal("100.00")
        payment.currency = "RUB"
        payment.category_id = 1
        payment.payment_type = "INCOME"
        payment.schedule_type = "daily"
        payment.schedule_config = {}
        payment.start_date = date(2025, 1, 1)
        payment.end_date = date(2025, 12, 31)
        payment.status = "active"
        payment.last_executed = datetime(2025, 3, 15, 0, 1, 0)
        payment.next_execution = date(2025, 3, 16)
        payment.created_at = datetime(2025, 1, 1)
        payment.updated_at = datetime(2025, 3, 15)

        result = payment.to_dict()
        assert result["end_date"] == "2025-12-31"
        assert result["last_executed"] == "2025-03-15T00:01:00"

    def test_tablename(self):
        assert RecurringPayment.__tablename__ == "recurring_payments"

    def test_to_dict_with_none_dates(self):
        payment = RecurringPayment()
        payment.id = uuid4()
        payment.user_id = 1
        payment.name = "Test"
        payment.description = None
        payment.amount = Decimal("100.00")
        payment.currency = "USD"
        payment.category_id = 1
        payment.payment_type = "EXPENSE"
        payment.schedule_type = "daily"
        payment.schedule_config = {}
        payment.start_date = None
        payment.end_date = None
        payment.status = "active"
        payment.last_executed = None
        payment.next_execution = None
        payment.created_at = None
        payment.updated_at = None

        result = payment.to_dict()
        assert result["start_date"] is None
        assert result["next_execution"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None


class TestPaymentScheduleModel:
    def test_repr(self):
        schedule = PaymentSchedule()
        schedule.id = uuid4()
        schedule.execution_date = date(2025, 1, 15)
        schedule.status = "executed"
        repr_str = repr(schedule)
        assert "2025-01-15" in repr_str
        assert "executed" in repr_str

    def test_to_dict(self):
        schedule_id = uuid4()
        payment_id = uuid4()
        schedule = PaymentSchedule()
        schedule.id = schedule_id
        schedule.recurring_payment_id = payment_id
        schedule.execution_date = date(2025, 1, 15)
        schedule.status = "executed"
        schedule.created_expense_id = 101
        schedule.created_income_id = None
        schedule.error_message = None
        schedule.executed_at = datetime(2025, 1, 15, 0, 1, 0)
        schedule.created_at = datetime(2025, 1, 1)
        schedule.updated_at = datetime(2025, 1, 15)

        result = schedule.to_dict()
        assert result["id"] == str(schedule_id)
        assert result["recurring_payment_id"] == str(payment_id)
        assert result["execution_date"] == "2025-01-15"
        assert result["status"] == "executed"
        assert result["created_expense_id"] == "101"
        assert result["created_income_id"] is None
        assert result["error_message"] is None
        assert result["executed_at"] == "2025-01-15T00:01:00"

    def test_to_dict_with_failed_status(self):
        schedule = PaymentSchedule()
        schedule.id = uuid4()
        schedule.recurring_payment_id = uuid4()
        schedule.execution_date = date(2025, 2, 15)
        schedule.status = "failed"
        schedule.created_expense_id = None
        schedule.created_income_id = None
        schedule.error_message = "Service unavailable"
        schedule.executed_at = None
        schedule.created_at = datetime(2025, 2, 15)
        schedule.updated_at = datetime(2025, 2, 15)

        result = schedule.to_dict()
        assert result["status"] == "failed"
        assert result["error_message"] == "Service unavailable"
        assert result["executed_at"] is None

    def test_to_dict_with_income_id(self):
        schedule = PaymentSchedule()
        schedule.id = uuid4()
        schedule.recurring_payment_id = uuid4()
        schedule.execution_date = date(2025, 3, 25)
        schedule.status = "executed"
        schedule.created_expense_id = None
        schedule.created_income_id = 202
        schedule.error_message = None
        schedule.executed_at = datetime(2025, 3, 25, 0, 1, 0)
        schedule.created_at = datetime(2025, 3, 25)
        schedule.updated_at = datetime(2025, 3, 25)

        result = schedule.to_dict()
        assert result["created_expense_id"] is None
        assert result["created_income_id"] == "202"

    def test_tablename(self):
        assert PaymentSchedule.__tablename__ == "payment_schedules"

    def test_to_dict_with_none_dates(self):
        schedule = PaymentSchedule()
        schedule.id = uuid4()
        schedule.recurring_payment_id = uuid4()
        schedule.execution_date = None
        schedule.status = "pending"
        schedule.created_expense_id = None
        schedule.created_income_id = None
        schedule.error_message = None
        schedule.executed_at = None
        schedule.created_at = None
        schedule.updated_at = None

        result = schedule.to_dict()
        assert result["execution_date"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None
