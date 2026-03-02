"""E2E tests for recurring payment CRUD, schedule, and statistics."""
import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.recurring


class TestRecurringPaymentCRUD:

    async def _create_recurring(self, pro_recurring_client, pro_shared_expense_category, **overrides):
        payload = {
            "name": "E2E Recurring Test",
            "amount": 50.00,
            "currency": "USD",
            "category_id": pro_shared_expense_category["id"],
            "payment_type": "EXPENSE",
            "schedule_type": "monthly",
            "schedule_config": {"day_of_month": 15},
            "start_date": date.today().isoformat(),
            **overrides,
        }
        return (await pro_recurring_client.create(**payload)).raise_on_error()

    async def test_create_monthly_payment(self, pro_recurring_client, pro_shared_expense_category):
        data = await self._create_recurring(
            pro_recurring_client, pro_shared_expense_category, name="Monthly Rent"
        )
        assert data["name"] == "Monthly Rent"
        assert data["schedule_type"] == "monthly"
        assert data["status"] == "active"
        assert "id" in data

    async def test_create_weekly_payment(self, pro_recurring_client, pro_shared_expense_category):
        data = await self._create_recurring(
            pro_recurring_client,
            pro_shared_expense_category,
            name="Weekly Groceries",
            schedule_type="weekly",
            schedule_config={"day_of_week": 1},
        )
        assert data["schedule_type"] == "weekly"

    async def test_create_yearly_payment(self, pro_recurring_client, pro_shared_expense_category):
        data = await self._create_recurring(
            pro_recurring_client,
            pro_shared_expense_category,
            name="Annual Insurance",
            schedule_type="yearly",
            schedule_config={"month": 6, "day": 1},
        )
        assert data["schedule_type"] == "yearly"

    async def test_create_income_recurring(self, pro_recurring_client, pro_shared_income_category):
        data = await self._create_recurring(
            pro_recurring_client,
            pro_shared_income_category,
            name="Monthly Salary",
            payment_type="INCOME",
            category_id=pro_shared_income_category["id"],
        )
        assert data["payment_type"] == "INCOME"

    async def test_list_recurring_payments(self, pro_recurring_client, pro_shared_expense_category):
        await self._create_recurring(
            pro_recurring_client, pro_shared_expense_category, name="Listed Recurring"
        )
        result = await pro_recurring_client.list_all()
        data = result.raise_on_error()
        assert "items" in data
        assert data["total"] >= 1

    async def test_get_recurring_payment(self, pro_recurring_client, pro_shared_expense_category):
        created = await self._create_recurring(
            pro_recurring_client, pro_shared_expense_category, name="Fetch Recurring"
        )
        result = await pro_recurring_client.get(created["id"])
        data = result.raise_on_error()
        assert data["id"] == created["id"]

    async def test_update_recurring_payment(self, pro_recurring_client, pro_shared_expense_category):
        created = await self._create_recurring(
            pro_recurring_client, pro_shared_expense_category, name="Before Update"
        )
        result = await pro_recurring_client.update(created["id"], name="After Update", amount=75.00)
        data = result.raise_on_error()
        assert data["name"] == "After Update"

    async def test_delete_recurring_payment(self, pro_recurring_client, pro_shared_expense_category):
        created = await self._create_recurring(
            pro_recurring_client, pro_shared_expense_category, name="Delete Recurring"
        )
        result = await pro_recurring_client.delete(created["id"])
        assert result.status_code == 204

    async def test_create_invalid_schedule_config(self, pro_recurring_client, pro_shared_expense_category):
        result = await pro_recurring_client.create(
            name="Bad Config",
            amount=10.00,
            currency="USD",
            category_id=pro_shared_expense_category["id"],
            payment_type="EXPENSE",
            schedule_type="weekly",
            schedule_config={},  # missing day_of_week
            start_date=date.today().isoformat(),
        )
        assert not result.ok


class TestRecurringPauseResume:

    async def _create_active(self, pro_recurring_client, pro_shared_expense_category):
        return (await pro_recurring_client.create(
            name="Pause Test",
            amount=30.00,
            currency="USD",
            category_id=pro_shared_expense_category["id"],
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 1},
            start_date=date.today().isoformat(),
        )).raise_on_error()

    async def test_pause_payment(self, pro_recurring_client, pro_shared_expense_category):
        created = await self._create_active(pro_recurring_client, pro_shared_expense_category)
        result = await pro_recurring_client.pause(created["id"])
        data = result.raise_on_error()
        assert "message" in data

        fetched = (await pro_recurring_client.get(created["id"])).raise_on_error()
        assert fetched["status"] == "paused"

    async def test_resume_payment(self, pro_recurring_client, pro_shared_expense_category):
        created = await self._create_active(pro_recurring_client, pro_shared_expense_category)
        await pro_recurring_client.pause(created["id"])
        result = await pro_recurring_client.resume(created["id"])
        data = result.raise_on_error()
        assert "message" in data

        fetched = (await pro_recurring_client.get(created["id"])).raise_on_error()
        assert fetched["status"] == "active"


class TestRecurringSchedules:

    async def test_get_schedules(self, pro_recurring_client, pro_shared_expense_category):
        created = (await pro_recurring_client.create(
            name="Schedule Test",
            amount=100.00,
            currency="USD",
            category_id=pro_shared_expense_category["id"],
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 10},
            start_date=date.today().isoformat(),
        )).raise_on_error()

        result = await pro_recurring_client.get_schedules(created["id"])
        data = result.raise_on_error()
        assert "items" in data


class TestRecurringStatistics:

    async def test_get_statistics(self, pro_recurring_client, pro_shared_expense_category):
        await pro_recurring_client.create(
            name="Stats Recurring",
            amount=45.00,
            currency="USD",
            category_id=pro_shared_expense_category["id"],
            payment_type="EXPENSE",
            schedule_type="monthly",
            schedule_config={"day_of_month": 20},
            start_date=date.today().isoformat(),
        )
        result = await pro_recurring_client.get_statistics()
        data = result.raise_on_error()
        assert isinstance(data, dict)
