"""
Tests for app/routers/internal.py — internal API endpoints.
Covers account validation, internal account fetch, AI summary, and balance update.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from starlette import status
from uuid import UUID

from app.main import app
from app.dependencies import get_account_service_internal
from app.services.account import AccountService
from app.tests.conftest import (
    TEST_WORKSPACE_ID,
    INTERNAL_TOKEN,
    INTERNAL_HEADERS,
    TestingSessionLocal,
    create_account_in_db,
)
from app.models.account import AccountType


# ---------------------------------------------------------------------------
# GET /internal/accounts/ai-summary
# ---------------------------------------------------------------------------


class TestGetAccountsAiSummary:
    def test_success(self, client: TestClient, db_session):
        user_id = 1
        create_account_in_db(
            db_session, owner_id=user_id, name="Savings", balance=5000.0,
            currency="USD", account_type=AccountType.SAVINGS,
        )
        create_account_in_db(
            db_session, owner_id=user_id, name="Checking", balance=2000.0,
            currency="EUR", account_type=AccountType.CHECKING,
        )

        response = client.get(
            f"/internal/accounts/ai-summary?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        names = [item["name"] for item in data["items"]]
        assert "Savings" in names
        assert "Checking" in names

    def test_empty_accounts(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/ai-summary?user_id=999&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["items"] == []

    def test_excludes_inactive_accounts(self, client: TestClient, db_session):
        user_id = 1
        create_account_in_db(
            db_session, owner_id=user_id, name="Active", is_active=True,
        )
        create_account_in_db(
            db_session, owner_id=user_id, name="Inactive", is_active=False,
        )

        response = client.get(
            f"/internal/accounts/ai-summary?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert "Active" in names
        assert "Inactive" not in names

    def test_missing_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/ai-summary?user_id=1&workspace_id={TEST_WORKSPACE_ID}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_wrong_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/ai-summary?user_id=1&workspace_id={TEST_WORKSPACE_ID}",
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_user_id_returns_422(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/ai-summary?workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_user_id_returns_422(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/ai-summary?user_id=-1&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_response_contains_expected_fields(self, client: TestClient, db_session):
        user_id = 1
        create_account_in_db(
            db_session, owner_id=user_id, name="Test",
            balance=100.0, currency="GBP", account_type=AccountType.BANK,
        )

        response = client.get(
            f"/internal/accounts/ai-summary?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        data = response.json()
        item = data["items"][0]
        assert "name" in item
        assert "type" in item
        assert "balance" in item
        assert "currency" in item
        assert item["type"] == "bank"
        assert item["currency"] == "GBP"
        assert item["balance"] == 100.0


# ---------------------------------------------------------------------------
# GET /internal/accounts/{account_id}/validate
# ---------------------------------------------------------------------------


class TestValidateAccountInternal:
    def test_success(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, name="Validated",
            account_type=AccountType.SAVINGS, balance=500.0,
        )

        response = client.get(
            f"/internal/accounts/{account.id}/validate"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["account"]["id"] == account.id
        assert data["account"]["name"] == "Validated"
        assert data["account"]["type"] == "savings"

    def test_not_found(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/99999/validate?user_id=1&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_missing_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/1/validate?user_id=1&workspace_id={TEST_WORKSPACE_ID}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_wrong_workspace_not_found(self, client: TestClient, db_session):
        user_id = 1
        other_workspace = UUID("660e8400-e29b-41d4-a716-446655440000")
        account = create_account_in_db(
            db_session, owner_id=user_id, workspace_id=other_workspace,
        )

        response = client.get(
            f"/internal/accounts/{account.id}/validate"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# GET /internal/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestGetAccountInternal:
    def test_success(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, name="Internal Fetch",
        )

        response = client.get(
            f"/internal/accounts/{account.id}"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account.id
        assert data["name"] == "Internal Fetch"

    def test_not_found(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/99999?user_id=1&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_missing_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/accounts/1?user_id=1&workspace_id={TEST_WORKSPACE_ID}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# PUT /internal/accounts/{account_id}/balance
# ---------------------------------------------------------------------------


class TestUpdateBalanceInternal:
    def test_same_currency_add(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, balance=1000.0, currency="USD",
        )

        with patch(
            "shared.clients.currency_service.CurrencyServiceClient.convert_amount",
            return_value=None,
        ):
            response = client.put(
                f"/internal/accounts/{account.id}/balance"
                f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}"
                f"&amount_change=200&transaction_currency=USD",
                headers=INTERNAL_HEADERS,
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["balance"] == 1200.0

    def test_same_currency_subtract(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, balance=1000.0, currency="USD",
        )

        response = client.put(
            f"/internal/accounts/{account.id}/balance"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}"
            f"&amount_change=-300&transaction_currency=USD",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["balance"] == 700.0

    def test_not_found(self, client: TestClient):
        response = client.put(
            f"/internal/accounts/99999/balance"
            f"?user_id=1&workspace_id={TEST_WORKSPACE_ID}"
            f"&amount_change=100&transaction_currency=USD",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_missing_token_returns_403(self, client: TestClient):
        response = client.put(
            f"/internal/accounts/1/balance"
            f"?user_id=1&workspace_id={TEST_WORKSPACE_ID}"
            f"&amount_change=100&transaction_currency=USD"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_archived_account_returns_400(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, is_archived=True, balance=1000.0,
        )

        response = client.put(
            f"/internal/accounts/{account.id}/balance"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}"
            f"&amount_change=100&transaction_currency=USD",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_insufficient_funds(self, client: TestClient, db_session):
        user_id = 1
        account = create_account_in_db(
            db_session, owner_id=user_id, balance=100.0, currency="USD",
        )

        response = client.put(
            f"/internal/accounts/{account.id}/balance"
            f"?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID}"
            f"&amount_change=-200&transaction_currency=USD",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
