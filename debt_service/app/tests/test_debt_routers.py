"""
Unit tests for Debt API Routers.

Tests cover:
- POST /debts/ - Create debt
- GET /debts/ - List debts
- GET /debts/{debt_id} - Get debt
- PUT /debts/{debt_id} - Update debt
- DELETE /debts/{debt_id} - Delete debt
- POST /debts/{debt_id}/payments/ - Create payment
- GET /debts/{debt_id}/payments/ - List payments
- GET /debts/summary/ - Get debt summary
- Input validation (422 errors)
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.debt import Debt, Contact, DebtPayment


class TestCreateDebtEndpoint:
    """Tests for POST /debts/"""

    @patch("app.services.debt.DebtService.create_debt")
    def test_create_debt_success(self, mock_create, client):
        """Successfully create a debt via API."""
        from app.schemas.debt import DebtResponse
        from datetime import datetime

        mock_response = DebtResponse(
            id=1,
            name="Test Loan",
            description="A loan",
            debt_type="LOAN",
            contact_id=None,
            category_id=None,
            currency="USD",
            initial_amount=10000.00,
            interest_rate=5.0,
            minimum_payment=200.00,
            start_date=date(2024, 1, 1),
            due_date=date(2029, 1, 1),
            user_id=1,
            workspace_id=client.workspace_id,
            current_balance=10000.00,
            last_payment_date=None,
            is_active=True,
            is_paid_off=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            payment_count=0,
            contact=None,
            is_read_only=False,
        )
        mock_create.return_value = mock_response

        response = client.post(
            "/debts/",
            json={
                "name": "Test Loan",
                "description": "A loan",
                "debt_type": "LOAN",
                "currency": "USD",
                "initial_amount": 10000.00,
                "interest_rate": 5.0,
                "minimum_payment": 200.00,
                "start_date": "2024-01-01",
                "due_date": "2029-01-01",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Loan"
        assert data["initial_amount"] == 10000.0
        assert data["is_active"] is True

    def test_create_debt_missing_required_field(self, client):
        """Reject request missing required fields."""
        response = client.post(
            "/debts/",
            json={
                "name": "Incomplete",
                # missing debt_type, currency, initial_amount, start_date
            },
        )

        assert response.status_code == 422

    def test_create_debt_invalid_amount(self, client):
        """Reject negative initial amount."""
        response = client.post(
            "/debts/",
            json={
                "name": "Bad Amount",
                "debt_type": "LOAN",
                "currency": "USD",
                "initial_amount": -100.00,
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 422

    def test_create_debt_invalid_debt_type(self, client):
        """Reject invalid debt type."""
        response = client.post(
            "/debts/",
            json={
                "name": "Bad Type",
                "debt_type": "INVALID_TYPE",
                "currency": "USD",
                "initial_amount": 1000.00,
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 422

    def test_create_debt_invalid_currency(self, client):
        """Reject invalid currency code."""
        response = client.post(
            "/debts/",
            json={
                "name": "Bad Currency",
                "debt_type": "LOAN",
                "currency": "TOOLONG",
                "initial_amount": 1000.00,
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 422

    def test_create_debt_interest_rate_over_100(self, client):
        """Reject interest rate over 100%."""
        response = client.post(
            "/debts/",
            json={
                "name": "High Rate",
                "debt_type": "LOAN",
                "currency": "USD",
                "initial_amount": 1000.00,
                "interest_rate": 150.0,
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 422


class TestGetDebtsEndpoint:
    """Tests for GET /debts/"""

    @patch("app.services.debt.DebtService.get_debts")
    @patch("app.services.debt.DebtService._get_ordered_ids")
    @patch("app.services.debt.SubscriptionClient")
    def test_get_debts_success(self, mock_sub_cls, mock_ordered, mock_get, client):
        """Successfully list debts."""
        mock_get.return_value = []
        mock_ordered.return_value = []

        response = client.get("/debts/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_debts_with_filters(self, client):
        """List debts with query parameters."""
        with patch("app.services.debt.DebtService.get_debts") as mock_get, \
             patch("app.services.debt.DebtService._get_ordered_ids") as mock_ordered:
            mock_get.return_value = []
            mock_ordered.return_value = []

            response = client.get("/debts/?skip=10&limit=5&active_only=true")

            assert response.status_code == 200
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][2] == 10  # skip
            assert call_args[0][3] == 5   # limit
            assert call_args[0][4] is True  # active_only

    def test_get_debts_negative_skip_rejected(self, client):
        """Reject negative skip parameter."""
        response = client.get("/debts/?skip=-1")

        assert response.status_code == 422

    def test_get_debts_limit_too_large_rejected(self, client):
        """Reject limit exceeding 1000."""
        response = client.get("/debts/?limit=1001")

        assert response.status_code == 422


class TestGetDebtEndpoint:
    """Tests for GET /debts/{debt_id}"""

    @patch("app.services.debt.DebtService.get_debt")
    def test_get_debt_success(self, mock_get, client):
        """Successfully get a specific debt."""
        from app.schemas.debt import DebtResponse
        from datetime import datetime

        mock_response = DebtResponse(
            id=1,
            name="Test Debt",
            debt_type="LOAN",
            contact_id=None,
            category_id=None,
            currency="USD",
            initial_amount=1000.0,
            interest_rate=None,
            minimum_payment=None,
            start_date=date(2024, 1, 1),
            due_date=None,
            user_id=1,
            workspace_id=client.workspace_id,
            current_balance=1000.0,
            last_payment_date=None,
            is_active=True,
            is_paid_off=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            payment_count=0,
            contact=None,
            is_read_only=False,
        )
        mock_get.return_value = mock_response

        response = client.get("/debts/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    @patch("app.services.debt.DebtService.get_debt")
    def test_get_debt_not_found(self, mock_get, client):
        """Return 404 for non-existent debt."""
        from app.exceptions import DebtNotFoundError
        mock_get.side_effect = DebtNotFoundError(99999)

        response = client.get("/debts/99999")

        assert response.status_code == 404


class TestUpdateDebtEndpoint:
    """Tests for PUT /debts/{debt_id}"""

    @patch("app.services.debt.DebtService.update_debt")
    def test_update_debt_success(self, mock_update, client):
        """Successfully update a debt."""
        from app.schemas.debt import DebtResponse
        from datetime import datetime

        mock_response = DebtResponse(
            id=1,
            name="Updated Debt",
            debt_type="LOAN",
            contact_id=None,
            category_id=None,
            currency="USD",
            initial_amount=1000.0,
            interest_rate=None,
            minimum_payment=None,
            start_date=date(2024, 1, 1),
            due_date=None,
            user_id=1,
            workspace_id=client.workspace_id,
            current_balance=1000.0,
            last_payment_date=None,
            is_active=True,
            is_paid_off=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            payment_count=0,
            contact=None,
            is_read_only=False,
        )
        mock_update.return_value = mock_response

        response = client.put(
            "/debts/1",
            json={"name": "Updated Debt"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Debt"

    @patch("app.services.debt.DebtService.update_debt")
    def test_update_debt_not_found(self, mock_update, client):
        """Return 404 for updating non-existent debt."""
        from app.exceptions import DebtNotFoundError
        mock_update.side_effect = DebtNotFoundError(99999)

        response = client.put("/debts/99999", json={"name": "Ghost"})

        assert response.status_code == 404

    @patch("app.services.debt.DebtService.update_debt")
    def test_update_debt_read_only(self, mock_update, client):
        """Return 403 for read-only debt."""
        from app.exceptions import DebtReadOnlyExcessError
        mock_update.side_effect = DebtReadOnlyExcessError(1, 10, 5)

        response = client.put("/debts/1", json={"name": "Cannot Edit"})

        assert response.status_code == 403

    def test_update_debt_empty_name_rejected(self, client):
        """Reject empty name."""
        response = client.put("/debts/1", json={"name": ""})

        assert response.status_code == 422

    def test_update_debt_invalid_interest_rate(self, client):
        """Reject interest rate over 100."""
        response = client.put("/debts/1", json={"interest_rate": 200.0})

        assert response.status_code == 422


class TestDeleteDebtEndpoint:
    """Tests for DELETE /debts/{debt_id}"""

    @patch("app.services.debt.DebtService.delete_debt")
    def test_delete_debt_success(self, mock_delete, client):
        """Successfully delete a debt."""
        mock_delete.return_value = True

        response = client.delete("/debts/1")

        assert response.status_code == 204

    @patch("app.services.debt.DebtService.delete_debt")
    def test_delete_debt_not_found(self, mock_delete, client):
        """Return 404 for non-existent debt."""
        from app.exceptions import DebtNotFoundError
        mock_delete.side_effect = DebtNotFoundError(99999)

        response = client.delete("/debts/99999")

        assert response.status_code == 404


class TestCreatePaymentEndpoint:
    """Tests for POST /debts/{debt_id}/payments/"""

    @patch("app.services.debt.DebtService.create_payment")
    def test_create_payment_success(self, mock_create, client):
        """Successfully create a payment."""
        from app.schemas.debt import DebtPaymentResponse
        from datetime import datetime

        mock_response = DebtPaymentResponse(
            id=1,
            debt_id=1,
            user_id=1,
            amount=200.00,
            principal_amount=150.00,
            interest_amount=50.00,
            payment_date=date(2024, 3, 1),
            description="March payment",
            payment_method="TRANSFER",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_create.return_value = mock_response

        response = client.post(
            "/debts/1/payments/",
            json={
                "amount": 200.00,
                "principal_amount": 150.00,
                "interest_amount": 50.00,
                "payment_date": "2024-03-01",
                "description": "March payment",
                "payment_method": "TRANSFER",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 200.0
        assert data["debt_id"] == 1

    def test_create_payment_missing_amount(self, client):
        """Reject payment without amount."""
        response = client.post(
            "/debts/1/payments/",
            json={
                "payment_date": "2024-03-01",
            },
        )

        assert response.status_code == 422

    def test_create_payment_negative_amount(self, client):
        """Reject negative payment amount."""
        response = client.post(
            "/debts/1/payments/",
            json={
                "amount": -50.00,
                "payment_date": "2024-03-01",
            },
        )

        assert response.status_code == 422

    def test_create_payment_zero_amount(self, client):
        """Reject zero payment amount."""
        response = client.post(
            "/debts/1/payments/",
            json={
                "amount": 0,
                "payment_date": "2024-03-01",
            },
        )

        assert response.status_code == 422

    def test_create_payment_invalid_method(self, client):
        """Reject invalid payment method."""
        response = client.post(
            "/debts/1/payments/",
            json={
                "amount": 100.00,
                "payment_date": "2024-03-01",
                "payment_method": "BITCOIN",
            },
        )

        assert response.status_code == 422

    @patch("app.services.debt.DebtService.create_payment")
    def test_create_payment_debt_not_found(self, mock_create, client):
        """Return 404 when debt does not exist."""
        from app.exceptions import DebtNotFoundError
        mock_create.side_effect = DebtNotFoundError(99999)

        response = client.post(
            "/debts/99999/payments/",
            json={
                "amount": 100.00,
                "payment_date": "2024-03-01",
            },
        )

        assert response.status_code == 404


class TestGetPaymentsEndpoint:
    """Tests for GET /debts/{debt_id}/payments/"""

    @patch("app.services.debt.DebtService.get_payments")
    @patch("app.services.debt.DebtService.get_debt")
    def test_get_payments_success(self, mock_get_debt, mock_get_payments, client):
        """Successfully list payments for a debt."""
        mock_get_debt.return_value = MagicMock()
        mock_get_payments.return_value = []

        response = client.get("/debts/1/payments/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("app.services.debt.DebtService.get_debt")
    def test_get_payments_debt_not_found(self, mock_get_debt, client):
        """Return 404 when debt does not exist."""
        from app.exceptions import DebtNotFoundError
        mock_get_debt.side_effect = DebtNotFoundError(99999)

        response = client.get("/debts/99999/payments/")

        assert response.status_code == 404


class TestDebtSummaryEndpoint:
    """Tests for GET /debts/summary/"""

    @patch("app.services.debt.DebtService.get_debt_summary")
    def test_get_summary_success(self, mock_summary, client):
        """Successfully get debt summary."""
        from app.schemas.debt import DebtSummary

        mock_summary.return_value = DebtSummary(
            total_debt=50000.0,
            total_payments=10000.0,
            active_debts=3,
            paid_off_debts=1,
            currency="USD",
            average_interest_rate=12.5,
        )

        response = client.get("/debts/summary/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_debt"] == 50000.0
        assert data["active_debts"] == 3
        assert data["currency"] == "USD"
        assert data["average_interest_rate"] == 12.5
