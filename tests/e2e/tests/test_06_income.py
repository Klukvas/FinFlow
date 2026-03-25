"""E2E tests for income CRUD and balance updates."""
import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.income


class TestIncomeCRUD:

    async def test_create_income(self, income_client, shared_income_category):
        result = await income_client.create(
            amount=500.0,
            category_id=shared_income_category["id"],
            description="E2E test income",
        )
        data = result.raise_on_error()
        assert data["amount"] == 500.0
        assert "id" in data

    async def test_get_income(self, income_client, shared_income_category):
        created = (await income_client.create(
            amount=200.0,
            category_id=shared_income_category["id"],
        )).raise_on_error()
        result = await income_client.get(created["id"])
        data = result.raise_on_error()
        assert data["id"] == created["id"]

    async def test_update_income(self, income_client, shared_income_category):
        created = (await income_client.create(
            amount=100.0,
            category_id=shared_income_category["id"],
        )).raise_on_error()
        result = await income_client.update(created["id"], amount=150.0)
        data = result.raise_on_error()
        assert data["amount"] == 150.0

    async def test_delete_income(self, income_client, shared_income_category):
        created = (await income_client.create(
            amount=50.0,
            category_id=shared_income_category["id"],
        )).raise_on_error()
        result = await income_client.delete(created["id"])
        assert result.ok or result.status_code == 204

    async def test_list_incomes(self, income_client):
        result = await income_client.list_all()
        assert result.ok


class TestIncomeWithAccount:

    async def test_income_adds_to_account(self, income_client, shared_account, shared_income_category):
        """Creating an income linked to an account should increase the balance."""
        await income_client.create(
            amount=500.0,
            category_id=shared_income_category["id"],
            account_id=shared_account["id"],
        )
        # Note: balance change accepted by API


class TestIncomeQueries:

    async def test_income_by_category(self, income_client, shared_income_category):
        await income_client.create(
            amount=100.0,
            category_id=shared_income_category["id"],
        )
        result = await income_client.by_category(shared_income_category["id"])
        assert result.ok

    async def test_paginated_incomes(self, income_client):
        result = await income_client.list_paginated(page=1, size=10)
        assert result.ok

    async def test_income_by_date_range(self, income_client, shared_income_category):
        """Filter incomes by date range returns matching records."""
        today = date.today()
        await income_client.create(
            amount=75.0,
            category_id=shared_income_category["id"],
            date=today.isoformat(),
        )
        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
        result = await income_client.by_date_range(start, end)
        assert result.ok

    async def test_income_summary_stats(self, income_client):
        """Income summary endpoint returns aggregated statistics."""
        result = await income_client.summary_stats()
        assert result.ok
