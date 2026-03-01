"""E2E tests for debt CRUD, contacts, and payments."""
import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.debt


class TestContactCRUD:

    async def test_create_contact(self, debt_client):
        result = await debt_client.create_contact(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            company="Acme Corp",
        )
        data = result.raise_on_error()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert "id" in data

    async def test_list_contacts(self, debt_client):
        await debt_client.create_contact(name="List Contact")
        result = await debt_client.list_contacts()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_contact(self, debt_client):
        created = (await debt_client.create_contact(name="Get Contact")).raise_on_error()
        result = await debt_client.get_contact(created["id"])
        data = result.raise_on_error()
        assert data["id"] == created["id"]
        assert data["name"] == "Get Contact"

    async def test_update_contact(self, debt_client):
        created = (await debt_client.create_contact(name="Old Name")).raise_on_error()
        result = await debt_client.update_contact(created["id"], name="New Name")
        data = result.raise_on_error()
        assert data["name"] == "New Name"

    async def test_delete_contact(self, debt_client):
        created = (await debt_client.create_contact(name="Delete Me")).raise_on_error()
        result = await debt_client.delete_contact(created["id"])
        assert result.status_code == 204

    async def test_get_nonexistent_contact(self, debt_client):
        result = await debt_client.get_contact(999999)
        assert not result.ok


class TestDebtCRUD:

    async def _create_test_debt(self, debt_client, **overrides):
        payload = {
            "name": "Test Loan",
            "debt_type": "LOAN",
            "currency": "USD",
            "initial_amount": 5000.00,
            "start_date": date.today().isoformat(),
            **overrides,
        }
        return (await debt_client.create_debt(**payload)).raise_on_error()

    async def test_create_debt(self, debt_client):
        data = await self._create_test_debt(debt_client, name="E2E Debt Create")
        assert data["name"] == "E2E Debt Create"
        assert data["debt_type"] == "LOAN"
        assert data["initial_amount"] == 5000.00
        assert "id" in data

    async def test_create_credit_card_debt(self, debt_client):
        data = await self._create_test_debt(
            debt_client,
            name="Visa Card",
            debt_type="CREDIT_CARD",
            interest_rate=18.99,
            minimum_payment=150.00,
            due_date=(date.today() + timedelta(days=365)).isoformat(),
        )
        assert data["debt_type"] == "CREDIT_CARD"
        assert data["interest_rate"] == 18.99

    async def test_create_debt_with_contact(self, debt_client):
        contact = (await debt_client.create_contact(name="Bank of Tests")).raise_on_error()
        data = await self._create_test_debt(
            debt_client, name="Debt With Contact", contact_id=contact["id"]
        )
        assert data["contact_id"] == contact["id"]

    async def test_list_debts(self, debt_client):
        await self._create_test_debt(debt_client, name="List Debt")
        result = await debt_client.list_debts()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_debt(self, debt_client):
        created = await self._create_test_debt(debt_client, name="Get Debt")
        result = await debt_client.get_debt(created["id"])
        data = result.raise_on_error()
        assert data["id"] == created["id"]

    async def test_update_debt(self, debt_client):
        created = await self._create_test_debt(debt_client, name="Before Update")
        result = await debt_client.update_debt(created["id"], name="After Update")
        data = result.raise_on_error()
        assert data["name"] == "After Update"

    async def test_delete_debt(self, debt_client):
        created = await self._create_test_debt(debt_client, name="Delete Debt")
        result = await debt_client.delete_debt(created["id"])
        assert result.status_code == 204

    async def test_get_nonexistent_debt(self, debt_client):
        result = await debt_client.get_debt(999999)
        assert not result.ok

    async def test_create_debt_invalid_type(self, debt_client):
        result = await debt_client.create_debt(
            name="Bad Debt",
            debt_type="INVALID_TYPE",
            currency="USD",
            initial_amount=100.0,
            start_date=date.today().isoformat(),
        )
        assert not result.ok

    async def test_create_debt_negative_amount(self, debt_client):
        result = await debt_client.create_debt(
            name="Negative Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=-100.0,
            start_date=date.today().isoformat(),
        )
        assert not result.ok


class TestDebtPayments:

    async def _create_debt_with_payment_setup(self, debt_client):
        debt = (await debt_client.create_debt(
            name="Payment Test Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=1000.00,
            start_date=date.today().isoformat(),
        )).raise_on_error()
        return debt

    async def test_create_payment(self, debt_client):
        debt = await self._create_debt_with_payment_setup(debt_client)
        result = await debt_client.create_payment(
            debt["id"],
            amount=200.00,
            payment_date=date.today().isoformat(),
            description="Monthly payment",
            payment_method="TRANSFER",
        )
        data = result.raise_on_error()
        assert data["amount"] == 200.00
        assert data["debt_id"] == debt["id"]

    async def test_create_payment_with_breakdown(self, debt_client):
        debt = await self._create_debt_with_payment_setup(debt_client)
        result = await debt_client.create_payment(
            debt["id"],
            amount=250.00,
            principal_amount=200.00,
            interest_amount=50.00,
            payment_date=date.today().isoformat(),
        )
        data = result.raise_on_error()
        assert data["principal_amount"] == 200.00
        assert data["interest_amount"] == 50.00

    async def test_list_payments(self, debt_client):
        debt = await self._create_debt_with_payment_setup(debt_client)
        await debt_client.create_payment(
            debt["id"],
            amount=100.00,
            payment_date=date.today().isoformat(),
        )
        result = await debt_client.list_payments(debt["id"])
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_payment_reduces_balance(self, debt_client):
        debt = await self._create_debt_with_payment_setup(debt_client)
        assert debt["current_balance"] == 1000.00
        await debt_client.create_payment(
            debt["id"],
            amount=300.00,
            payment_date=date.today().isoformat(),
        )
        updated = (await debt_client.get_debt(debt["id"])).raise_on_error()
        assert updated["current_balance"] < debt["current_balance"]


class TestDebtSummary:

    async def test_get_debt_summary(self, debt_client):
        # Create at least one debt so summary is meaningful
        await debt_client.create_debt(
            name="Summary Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=2000.00,
            start_date=date.today().isoformat(),
        )
        result = await debt_client.get_summary()
        data = result.raise_on_error()
        assert "total_debt" in data
        assert "active_debts" in data
        assert data["active_debts"] >= 1
