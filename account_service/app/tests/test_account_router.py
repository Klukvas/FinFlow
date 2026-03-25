"""
Tests for app/routers/account.py — public account API endpoints.
Covers all CRUD operations and edge cases via HTTP calls.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from starlette import status
from uuid import UUID

from app.tests.conftest import (
    TEST_WORKSPACE_ID,
    TestingSessionLocal,
    create_account_in_db,
)
from app.models.account import AccountType

WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}


def _auth_headers(user_id: int) -> dict:
    """Return Authorization + Workspace headers."""
    return {"Authorization": "Bearer test-token", **WORKSPACE_HEADER}


# ---------------------------------------------------------------------------
# POST /accounts/
# ---------------------------------------------------------------------------


class TestCreateAccountRoute:
    def test_success(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {
            "name": "My Savings",
            "type": "savings",
            "currency": "USD",
            "balance": 500.0,
        }

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "My Savings"
        assert data["type"] == "savings"
        assert data["currency"] == "USD"
        assert data["balance"] == 500.0
        assert data["is_active"] is True
        assert data["is_archived"] is False

    def test_minimal_payload(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"name": "Cash", "type": "cash"}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["currency"] == "USD"
        assert data["balance"] == 0.0

    def test_missing_name_returns_422(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"type": "cash"}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_type_returns_422(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"name": "Test"}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_type_returns_422(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"name": "Test", "type": "nonexistent"}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_balance_exceeds_max_returns_422(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"name": "Test", "type": "cash", "balance": 1000000000.0}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_no_auth_returns_401_or_403(self, client: TestClient):
        payload = {"name": "Test", "type": "cash"}
        response = client.post("/accounts/", json=payload, headers=WORKSPACE_HEADER)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_no_workspace_header_returns_400(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {"name": "Test", "type": "cash"}

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            # Override workspace to not inject it
            from app.main import app
            from app.dependencies import get_workspace_id as real_get_workspace_id

            # Remove workspace override temporarily
            original = app.dependency_overrides.get(real_get_workspace_id)
            if real_get_workspace_id in app.dependency_overrides:
                del app.dependency_overrides[real_get_workspace_id]

            try:
                response = client.post(
                    "/accounts/",
                    json=payload,
                    headers={"Authorization": "Bearer test-token"},
                )
                assert response.status_code == status.HTTP_400_BAD_REQUEST
            finally:
                if original is not None:
                    app.dependency_overrides[real_get_workspace_id] = original

    def test_all_account_types(self, client: TestClient):
        user_id = randint(1000, 2000)
        for account_type in AccountType:
            payload = {"name": f"Type {account_type.value}", "type": account_type.value}
            with patch("shared.auth.dependencies.decode_token", return_value=user_id):
                response = client.post(
                    "/accounts/", json=payload, headers=_auth_headers(user_id)
                )
            assert response.status_code == status.HTTP_201_CREATED, (
                f"Failed for type {account_type.value}"
            )

    def test_with_description(self, client: TestClient):
        user_id = randint(1000, 2000)
        payload = {
            "name": "Described",
            "type": "savings",
            "description": "My account description",
        }

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.post(
                "/accounts/", json=payload, headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["description"] == "My account description"


# ---------------------------------------------------------------------------
# GET /accounts/
# ---------------------------------------------------------------------------


class TestListAccountsRoute:
    def test_empty_list(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_returns_created_accounts(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        create_account_in_db(db_session, owner_id=user_id, name="Account 1")
        create_account_in_db(db_session, owner_id=user_id, name="Account 2")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_excludes_archived_by_default(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        create_account_in_db(db_session, owner_id=user_id, name="Active")
        create_account_in_db(db_session, owner_id=user_id, name="Archived", is_archived=True)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get("/accounts/", headers=_auth_headers(user_id))

        data = response.json()
        names = [a["name"] for a in data]
        assert "Active" in names
        assert "Archived" not in names

    def test_include_archived(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        create_account_in_db(db_session, owner_id=user_id, name="Active")
        create_account_in_db(db_session, owner_id=user_id, name="Archived", is_archived=True)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get(
                "/accounts/?include_archived=true", headers=_auth_headers(user_id)
            )

        data = response.json()
        names = [a["name"] for a in data]
        assert "Active" in names
        assert "Archived" in names


# ---------------------------------------------------------------------------
# GET /accounts/{account_id}
# ---------------------------------------------------------------------------


class TestGetAccountRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get(
                f"/accounts/{account.id}", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account.id

    def test_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get("/accounts/99999", headers=_auth_headers(user_id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_workspace_not_found(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        other_workspace = UUID("660e8400-e29b-41d4-a716-446655440000")
        account = create_account_in_db(
            db_session, owner_id=user_id, workspace_id=other_workspace
        )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get(
                f"/accounts/{account.id}", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# PUT /accounts/{account_id}
# ---------------------------------------------------------------------------


class TestUpdateAccountRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.put(
                f"/accounts/{account.id}",
                json={"name": "Updated Name"},
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Name"

    def test_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.put(
                "/accounts/99999",
                json={"name": "Ghost"},
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_archived_returns_400(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(
            db_session, owner_id=user_id, is_archived=True
        )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.put(
                f"/accounts/{account.id}",
                json={"name": "Nope"},
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(
            db_session, owner_id=user_id, balance=100.0
        )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.put(
                f"/accounts/{account.id}",
                json={"balance": 999.0},
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["balance"] == 999.0
        assert data["name"] == account.name  # unchanged


# ---------------------------------------------------------------------------
# PATCH /accounts/{account_id}/archive
# ---------------------------------------------------------------------------


class TestArchiveAccountRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                f"/accounts/{account.id}/archive", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_archived"] is True
        assert data["is_active"] is False

    def test_already_archived_returns_400(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(
            db_session, owner_id=user_id, is_archived=True
        )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                f"/accounts/{account.id}/archive", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                "/accounts/99999/archive", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# PATCH /accounts/{account_id}/balance
# ---------------------------------------------------------------------------


class TestUpdateBalanceRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id, balance=100.0)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                f"/accounts/{account.id}/balance?balance=999.99",
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["balance"] == 999.99

    def test_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                "/accounts/99999/balance?balance=100.0",
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_archived_returns_400(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(
            db_session, owner_id=user_id, is_archived=True
        )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.patch(
                f"/accounts/{account.id}/balance?balance=100.0",
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# GET /accounts/{account_id}/summary
# ---------------------------------------------------------------------------


class TestGetAccountSummaryRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "app.clients.expense_service_client.ExpenseServiceClient.get_expenses_by_account",
                 return_value=[],
             ), \
             patch(
                 "app.clients.income_service_client.IncomeServiceClient.get_incomes_by_account",
                 return_value=[],
             ):
            response = client.get(
                f"/accounts/{account.id}/summary", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account.id
        assert data["transaction_count"] == 0


# ---------------------------------------------------------------------------
# GET /accounts/{account_id}/transactions
# ---------------------------------------------------------------------------


class TestGetAccountTransactionsRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        account = create_account_in_db(db_session, owner_id=user_id)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "app.clients.expense_service_client.ExpenseServiceClient.get_expenses_by_account",
                 return_value=[],
             ), \
             patch(
                 "app.clients.income_service_client.IncomeServiceClient.get_incomes_by_account",
                 return_value=[],
             ):
            response = client.get(
                f"/accounts/{account.id}/transactions",
                headers=_auth_headers(user_id),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_income"] == 0.0
        assert data["total_expenses"] == 0.0
        assert data["transactions"] == []

    def test_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            response = client.get(
                "/accounts/99999/transactions", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# GET /accounts/summaries
# ---------------------------------------------------------------------------


class TestGetAccountSummariesRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        create_account_in_db(db_session, owner_id=user_id, name="Savings")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "app.clients.expense_service_client.ExpenseServiceClient.get_expenses_by_account",
                 return_value=[],
             ), \
             patch(
                 "app.clients.income_service_client.IncomeServiceClient.get_incomes_by_account",
                 return_value=[],
             ):
            response = client.get(
                "/accounts/summaries", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Savings"


# ---------------------------------------------------------------------------
# GET /accounts/statistics
# ---------------------------------------------------------------------------


class TestGetAccountStatisticsRoute:
    def test_success(self, client: TestClient, db_session):
        user_id = randint(1000, 2000)
        create_account_in_db(db_session, owner_id=user_id, balance=1000.0, currency="USD")

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.user_service.UserServiceClient.get_user_base_currency",
                 return_value="USD",
             ), \
             patch(
                 "shared.clients.currency_service.CurrencyServiceClient.get_rates",
                 return_value=None,
             ):
            response = client.get(
                "/accounts/statistics", headers=_auth_headers(user_id)
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_accounts"] == 1
        assert data["currency"] == "USD"
        assert data["total_balance"] == 1000.0
