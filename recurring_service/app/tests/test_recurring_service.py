"""Tests for RecurringPaymentService business logic."""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4, UUID

from app.services.recurring_payment_service import RecurringPaymentService
from app.schemas.recurring_payment import (
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
)
from app.models.recurring_payment import RecurringPayment
from app.models.payment_schedule import PaymentSchedule
from app.exceptions import (
    RecurringPaymentNotFoundError,
    CategoryNotFoundError,
    InvalidPaymentStatusError,
    RecurringLimitExceededError,
    RecurringReadOnlyExcessError,
)


TEST_USER_ID = 1
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def service():
    """Create a RecurringPaymentService with mocked dependencies."""
    with patch("app.services.recurring_payment_service.ExpenseServiceClient"), \
         patch("app.services.recurring_payment_service.IncomeServiceClient"), \
         patch("app.services.recurring_payment_service.CategoryServiceClient") as mock_cat_cls, \
         patch("shared.clients.subscription.SubscriptionClient.get_instance") as mock_sub:
        svc = RecurringPaymentService()
        # Mock category client
        svc.category_client.validate_category_exists = AsyncMock(return_value=True)
        # Mock subscription client
        svc.subscription_client.check_limit = MagicMock(return_value=(True, None))
        svc.subscription_client.check_modify_allowed = MagicMock(return_value=True)
        svc.subscription_client.get_user_features = MagicMock(
            return_value={"recurring": {"limit_value": 100}}
        )
        yield svc


@pytest.fixture
def mock_db(db_session):
    return db_session


class TestCreateRecurringPayment:
    @pytest.mark.asyncio
    async def test_creates_monthly_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Monthly Rent",
            amount=Decimal("1500.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 1},
            start_date=date(2025, 1, 1),
        )
        result = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.name == "Monthly Rent"
        assert result.amount == Decimal("1500.00")
        assert result.status == "active"
        assert result.user_id == TEST_USER_ID
        assert result.workspace_id == TEST_WORKSPACE_ID

    @pytest.mark.asyncio
    async def test_creates_daily_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Daily Coffee",
            amount=Decimal("5.00"),
            currency="USD",
            category_id=3,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        result = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.schedule_type == "daily"
        assert result.next_execution == date(2025, 1, 1)

    @pytest.mark.asyncio
    async def test_creates_income_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Monthly Salary",
            amount=Decimal("5000.00"),
            currency="USD",
            category_id=5,
            payment_type="INCOME",
            schedule_type="monthly",
            schedule_config={"day_of_month": 25},
            start_date=date(2025, 1, 25),
        )
        result = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.payment_type == "INCOME"

    @pytest.mark.asyncio
    async def test_raises_on_category_not_found(self, service, mock_db):
        service.category_client.validate_category_exists = AsyncMock(return_value=False)
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=999,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        with pytest.raises(CategoryNotFoundError):
            await service.create_recurring_payment(
                payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_raises_on_limit_exceeded(self, service, mock_db):
        service.subscription_client.check_limit = MagicMock(return_value=(False, 3))
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        with pytest.raises(RecurringLimitExceededError):
            await service.create_recurring_payment(
                payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_sets_next_execution_on_create(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Weekly Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="weekly",
            schedule_config={"day_of_week": 2},
            start_date=date(2025, 1, 6),  # Monday
        )
        result = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        # Wednesday from Monday Jan 6
        assert result.next_execution == date(2025, 1, 8)


class TestGetRecurringPayments:
    def test_returns_empty_list(self, service, mock_db):
        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.total == 0
        assert result.items == []
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_returns_created_payments(self, service, mock_db):
        # Create two payments
        for name in ["Payment 1", "Payment 2"]:
            payment_data = RecurringPaymentCreate(
                name=name,
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="daily",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )
            await service.create_recurring_payment(
                payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_filters_by_status(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Active Payment",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db, status="active"
        )
        assert result.total == 1

        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db, status="paused"
        )
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_filters_by_payment_type(self, service, mock_db):
        for ptype in ["EXPENSE", "INCOME"]:
            payment_data = RecurringPaymentCreate(
                name=f"{ptype} Payment",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type=ptype,
                schedule_type="daily",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )
            await service.create_recurring_payment(
                payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db, payment_type="EXPENSE"
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_pagination(self, service, mock_db):
        for i in range(5):
            payment_data = RecurringPaymentCreate(
                name=f"Payment {i}",
                amount=Decimal("100.00"),
                currency="USD",
                category_id=1,
                payment_type="EXPENSE",
                schedule_type="daily",
                schedule_config={},
                start_date=date(2025, 1, 1),
            )
            await service.create_recurring_payment(
                payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

        result = service.get_recurring_payments(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db, page=1, size=2
        )
        assert result.total == 5
        assert len(result.items) == 2
        assert result.pages == 3


class TestGetRecurringPayment:
    @pytest.mark.asyncio
    async def test_returns_payment_by_id(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Find Me",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        result = service.get_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.id == created.id
        assert result.name == "Find Me"

    def test_raises_when_not_found(self, service, mock_db):
        with pytest.raises(RecurringPaymentNotFoundError):
            service.get_recurring_payment(
                uuid4(), TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestUpdateRecurringPayment:
    @pytest.mark.asyncio
    async def test_updates_name(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Original",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        update_data = RecurringPaymentUpdate(name="Updated")
        updated = await service.update_recurring_payment(
            created.id, update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert updated.name == "Updated"

    @pytest.mark.asyncio
    async def test_updates_amount(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        update_data = RecurringPaymentUpdate(amount=Decimal("200.00"))
        updated = await service.update_recurring_payment(
            created.id, update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert updated.amount == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, service, mock_db):
        update_data = RecurringPaymentUpdate(name="Updated")
        with pytest.raises(RecurringPaymentNotFoundError):
            await service.update_recurring_payment(
                uuid4(), update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_validates_new_category(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        service.category_client.validate_category_exists = AsyncMock(return_value=False)
        update_data = RecurringPaymentUpdate(category_id=999)
        with pytest.raises(CategoryNotFoundError):
            await service.update_recurring_payment(
                created.id, update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_recalculates_next_execution_on_schedule_change(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        original_next = created.next_execution

        update_data = RecurringPaymentUpdate(
            schedule_type="monthly",
            schedule_config={"day_of_month": 15},
        )
        updated = await service.update_recurring_payment(
            created.id, update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert updated.next_execution != original_next

    @pytest.mark.asyncio
    async def test_raises_read_only_excess(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        service.subscription_client.check_modify_allowed = MagicMock(return_value=False)
        update_data = RecurringPaymentUpdate(name="New Name")
        with pytest.raises(RecurringReadOnlyExcessError):
            await service.update_recurring_payment(
                created.id, update_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestDeleteRecurringPayment:
    @pytest.mark.asyncio
    async def test_deletes_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="To Delete",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.delete_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        with pytest.raises(RecurringPaymentNotFoundError):
            service.get_recurring_payment(
                created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    def test_raises_when_not_found(self, service, mock_db):
        with pytest.raises(RecurringPaymentNotFoundError):
            service.delete_recurring_payment(
                uuid4(), TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestPauseRecurringPayment:
    @pytest.mark.asyncio
    async def test_pauses_active_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="To Pause",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.pause_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        payment = service.get_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert payment.status == "paused"

    def test_raises_when_not_found(self, service, mock_db):
        with pytest.raises(RecurringPaymentNotFoundError):
            service.pause_recurring_payment(
                uuid4(), TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_raises_when_not_active(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="To Pause",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        # First pause
        service.pause_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        # Second pause should fail
        with pytest.raises(InvalidPaymentStatusError):
            service.pause_recurring_payment(
                created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestResumeRecurringPayment:
    @pytest.mark.asyncio
    async def test_resumes_paused_payment(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="To Resume",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.pause_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.resume_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        payment = service.get_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert payment.status == "active"

    def test_raises_when_not_found(self, service, mock_db):
        with pytest.raises(RecurringPaymentNotFoundError):
            service.resume_recurring_payment(
                uuid4(), TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_raises_when_not_paused(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Active Payment",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        with pytest.raises(InvalidPaymentStatusError):
            service.resume_recurring_payment(
                created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )

    @pytest.mark.asyncio
    async def test_raises_read_only_excess_on_resume(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="To Resume",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.pause_recurring_payment(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        service.subscription_client.check_modify_allowed = MagicMock(return_value=False)
        with pytest.raises(RecurringReadOnlyExcessError):
            service.resume_recurring_payment(
                created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestGetPaymentSchedules:
    @pytest.mark.asyncio
    async def test_returns_empty_schedules(self, service, mock_db):
        payment_data = RecurringPaymentCreate(
            name="Test",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        created = await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        result = service.get_payment_schedules(
            created.id, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert result.total == 0
        assert result.items == []

    def test_raises_when_payment_not_found(self, service, mock_db):
        with pytest.raises(RecurringPaymentNotFoundError):
            service.get_payment_schedules(
                uuid4(), TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
            )


class TestGetPaymentStatistics:
    @pytest.mark.asyncio
    async def test_returns_statistics(self, service, mock_db):
        # Create an active payment
        payment_data = RecurringPaymentCreate(
            name="Active",
            amount=Decimal("100.00"),
            currency="USD",
            category_id=1,
            payment_type="EXPENSE",
            schedule_type="daily",
            schedule_config={},
            start_date=date(2025, 1, 1),
        )
        await service.create_recurring_payment(
            payment_data, TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )

        stats = service.get_payment_statistics(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert stats["total_payments"] == 1
        assert stats["active_payments"] == 1
        assert stats["paused_payments"] == 0
        assert "executed_this_month" in stats
        assert "failed_this_month" in stats

    def test_empty_statistics(self, service, mock_db):
        stats = service.get_payment_statistics(
            TEST_USER_ID, TEST_WORKSPACE_ID, mock_db
        )
        assert stats["total_payments"] == 0
        assert stats["active_payments"] == 0
