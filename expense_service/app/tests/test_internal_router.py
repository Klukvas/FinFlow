"""
Tests for app/routers/internal.py - the internal API endpoints.
Covers the 43% gap in the internal router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import date
from uuid import UUID

from app.main import app
from app.dependencies import get_expense_service_internal, verify_internal_token

INTERNAL_TOKEN = "test-internal-token"
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_TOKEN}
WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def _make_mock_service(expenses=None):
    """Create a mock ExpenseService for dependency injection."""
    from app.models.expense import Expense
    service = MagicMock()

    # Default: return an empty list for db queries
    query_chain = (
        service.db.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    query_chain.all.return_value = expenses or []

    return service


@pytest.fixture
def client():
    """TestClient with dependency overrides that inject a controllable service."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /internal/expenses/account/{account_id}
# ---------------------------------------------------------------------------

class TestGetExpensesByAccount:
    def test_success_empty_list(self, client):
        """Internal endpoint returns empty list when no expenses exist."""
        mock_service = _make_mock_service([])
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 200
        assert response.json() == []

    def test_missing_token_returns_403(self, client):
        response = client.get(f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}")
        assert response.status_code == 403

    def test_wrong_token_returns_403(self, client):
        response = client.get(
            f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}",
            headers={"X-Internal-Token": "wrong-token"}
        )
        assert response.status_code == 403

    def test_pagination_parameters_accepted(self, client):
        mock_service = _make_mock_service([])
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}&limit=5&offset=10",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 200

    def test_db_query_exception_returns_400(self, client):
        """When db.query raises an exception, endpoint returns 400."""
        mock_service = MagicMock()
        mock_service.db.query.side_effect = RuntimeError("db crash")

        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 400
        assert "error" in response.json()

    def test_limit_exceeds_max_returns_400(self, client):
        """limit > 1000 fails query parameter validation.
        The custom validation exception handler converts 422 -> 400."""
        mock_service = _make_mock_service([])
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}&limit=9999",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)
        # Custom exception handler maps 422 -> 400
        assert response.status_code == 400

    def test_offset_negative_returns_400(self, client):
        """offset < 0 fails query parameter validation -> 400 via custom handler."""
        mock_service = _make_mock_service([])
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                f"/internal/expenses/account/5?user_id=10&workspace_id={WORKSPACE_ID}&offset=-1",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /internal/expenses/account/{account_id}/validate
# ---------------------------------------------------------------------------

class TestValidateAccountForExpenses:
    def test_success(self, client):
        mock_service = MagicMock()
        mock_service.account_client.validate_account.return_value = {
            "account": {"id": 5, "currency": "USD", "name": "Savings"}
        }
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                "/internal/expenses/account/5/validate?user_id=10",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["account_id"] == 5
        assert data["user_id"] == 10
        assert "account" in data

    def test_missing_token_returns_403(self, client):
        response = client.get("/internal/expenses/account/5/validate?user_id=10")
        assert response.status_code == 403

    def test_account_service_exception_returns_400(self, client):
        mock_service = MagicMock()
        mock_service.account_client.validate_account.side_effect = Exception("account svc down")
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                "/internal/expenses/account/5/validate?user_id=10",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_account_data_included_in_response(self, client):
        """The 'account' key in response reflects data from account service."""
        mock_service = MagicMock()
        mock_service.account_client.validate_account.return_value = {
            "account": {"id": 5, "currency": "EUR", "balance": 1000.0}
        }
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.get(
                "/internal/expenses/account/5/validate?user_id=10",
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 200
        data = response.json()
        assert data["account"]["currency"] == "EUR"
        assert data["account"]["balance"] == 1000.0


# ---------------------------------------------------------------------------
# POST /internal/ (internal expense creation)
# ---------------------------------------------------------------------------

class TestInternalExpenseCreate:
    def test_missing_token_returns_403(self, client):
        response = client.post(
            f"/internal/?user_id=10&workspace_id={WORKSPACE_ID}",
            json={"amount": 50.0}
        )
        assert response.status_code == 403

    def test_invalid_token_returns_403(self, client):
        response = client.post(
            f"/internal/?user_id=10&workspace_id={WORKSPACE_ID}",
            json={"amount": 50.0},
            headers={"X-Internal-Token": "bad-token"}
        )
        assert response.status_code == 403

    def test_service_generic_exception_returns_400(self, client):
        """Generic service errors are caught and wrapped in ExpenseValidationError."""
        mock_service = MagicMock()
        mock_service.create.side_effect = Exception("unexpected failure")
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.post(
                f"/internal/?user_id=10&workspace_id={WORKSPACE_ID}",
                json={"amount": 50.0},
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 400
        assert "error" in response.json()

    def test_invalid_amount_returns_validation_error(self, client):
        """Amount <= 0 should fail Pydantic validation before reaching the service."""
        mock_service = MagicMock()
        app.dependency_overrides[get_expense_service_internal] = lambda: mock_service
        try:
            response = client.post(
                f"/internal/?user_id=10&workspace_id={WORKSPACE_ID}",
                json={"amount": -10.0},
                headers=INTERNAL_HEADERS
            )
        finally:
            app.dependency_overrides.pop(get_expense_service_internal, None)

        assert response.status_code == 400
