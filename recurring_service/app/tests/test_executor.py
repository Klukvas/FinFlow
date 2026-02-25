"""Tests for PaymentExecutor with mocked clients"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.executor import PaymentExecutor
from app.exceptions import PaymentExecutionError


@pytest.fixture
def expense_client():
    client = AsyncMock()
    client.create_expense = AsyncMock(return_value={"id": 101})
    return client


@pytest.fixture
def income_client():
    client = AsyncMock()
    client.create_income = AsyncMock(return_value={"id": 202})
    return client


@pytest.fixture
def category_client():
    client = AsyncMock()
    client.get_category = AsyncMock(return_value={"id": 1, "name": "Test"})
    return client


@pytest.fixture
def executor(expense_client, income_client, category_client):
    return PaymentExecutor(expense_client, income_client, category_client)


def make_recurring_payment(payment_type="EXPENSE"):
    """Create a mock recurring payment"""
    payment = MagicMock()
    payment.id = uuid4()
    payment.user_id = 1
    payment.workspace_id = uuid4()
    payment.name = "Test Payment"
    payment.amount = Decimal("100.00")
    payment.currency = "USD"
    payment.category_id = 1
    payment.payment_type = payment_type
    payment.status = "active"
    payment.next_execution = date(2025, 1, 1)
    payment.end_date = None
    payment.schedule_type = "monthly"
    return payment


class TestExecuteSinglePayment:
    @pytest.mark.asyncio
    async def test_expense_passes_currency_and_workspace(self, executor, expense_client):
        """Verify currency and workspace_id are passed when creating expense"""
        payment = make_recurring_payment("EXPENSE")
        execution_date = date(2025, 1, 1)

        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        with patch("app.services.executor.PaymentCalculator.calculate_next_execution", return_value=date(2025, 2, 1)):
            await executor._execute_single_payment(db, payment, execution_date)

        expense_client.create_expense.assert_called_once()
        call_args = expense_client.create_expense.call_args

        expense_data = call_args[0][0]
        assert expense_data["currency"] == "USD"
        assert expense_data["amount"] == 100.0
        assert expense_data["category_id"] == 1
        assert expense_data["date"] == "2025-01-01"

        # user_id and workspace_id passed as positional args
        assert call_args[0][1] == payment.user_id
        assert call_args[0][2] == str(payment.workspace_id)

    @pytest.mark.asyncio
    async def test_income_passes_currency_and_workspace(self, executor, income_client):
        """Verify currency and workspace_id are passed when creating income"""
        payment = make_recurring_payment("INCOME")
        execution_date = date(2025, 1, 1)

        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        with patch("app.services.executor.PaymentCalculator.calculate_next_execution", return_value=date(2025, 2, 1)):
            await executor._execute_single_payment(db, payment, execution_date)

        income_client.create_income.assert_called_once()
        call_args = income_client.create_income.call_args

        income_data = call_args[0][0]
        assert income_data["currency"] == "USD"
        assert income_data["amount"] == 100.0
        assert income_data["category_id"] == 1

        assert call_args[0][1] == payment.user_id
        assert call_args[0][2] == str(payment.workspace_id)

    @pytest.mark.asyncio
    async def test_category_validated_with_workspace(self, executor, category_client):
        """Verify category validation includes workspace_id"""
        payment = make_recurring_payment("EXPENSE")
        execution_date = date(2025, 1, 1)

        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        with patch("app.services.executor.PaymentCalculator.calculate_next_execution", return_value=date(2025, 2, 1)):
            await executor._execute_single_payment(db, payment, execution_date)

        category_client.get_category.assert_called_once_with(
            payment.category_id,
            payment.user_id,
            payment.workspace_id
        )

    @pytest.mark.asyncio
    async def test_schedule_marked_executed_on_success(self, executor):
        """Verify schedule status is set to executed on success"""
        payment = make_recurring_payment("EXPENSE")
        execution_date = date(2025, 1, 1)

        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        with patch("app.services.executor.PaymentCalculator.calculate_next_execution", return_value=date(2025, 2, 1)):
            await executor._execute_single_payment(db, payment, execution_date)

        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_marked_failed_on_client_error(self, executor, expense_client):
        """Verify schedule status is failed when client raises"""
        expense_client.create_expense.side_effect = Exception("Service unavailable")
        payment = make_recurring_payment("EXPENSE")
        execution_date = date(2025, 1, 1)

        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()

        with pytest.raises(PaymentExecutionError):
            await executor._execute_single_payment(db, payment, execution_date)

        db.commit.assert_called_once()
