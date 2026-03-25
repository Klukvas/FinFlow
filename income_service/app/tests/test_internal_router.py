"""
Tests for app/routers/internal.py — internal API endpoints.

These endpoints require X-Internal-Token authentication and provide
inter-service communication capabilities.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from fastapi.testclient import TestClient
from starlette import status

from app.main import app
from app.tests.conftest import (
    TEST_USER_ID,
    TEST_WORKSPACE_ID,
)

INTERNAL_TOKEN = "test-internal-token-income"
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_TOKEN}


# ---------------------------------------------------------------------------
# POST /internal/ (Create income internally)
# ---------------------------------------------------------------------------
class TestInternalIncomeCreate:
    def test_create_success(self, client: TestClient):
        payload = {
            "amount": 500.0,
            "currency": "USD",
            "description": "Recurring salary",
            "date": "2025-01-15",
        }
        response = client.post(
            f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            json=payload,
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 500.0
        assert data["user_id"] == TEST_USER_ID

    def test_create_without_token_returns_403(self, client: TestClient):
        payload = {"amount": 100.0, "date": "2025-01-15"}
        response = client.post(
            f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            json=payload,
        )
        assert response.status_code == 403

    def test_create_with_invalid_token_returns_403(self, client: TestClient):
        payload = {"amount": 100.0, "date": "2025-01-15"}
        response = client.post(
            f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            json=payload,
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == 403

    def test_create_limit_exceeded_returns_429(self, client: TestClient):
        payload = {"amount": 100.0, "date": "2025-01-15"}
        with patch(
            "shared.clients.subscription.SubscriptionClient.check_limit",
            return_value=(False, 10),
        ):
            response = client.post(
                f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
                json=payload,
                headers=INTERNAL_HEADERS,
            )

        assert response.status_code == 429
        data = response.json()
        # The http_exception_handler wraps detail under "error" key
        assert "INCOME_LIMIT_EXCEEDED" in str(data)

    def test_create_missing_user_id_returns_422(self, client: TestClient):
        payload = {"amount": 100.0, "date": "2025-01-15"}
        response = client.post(
            f"/internal/?workspace_id={TEST_WORKSPACE_ID}",
            json=payload,
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == 422

    def test_create_service_error_returns_500(self, client: TestClient):
        payload = {"amount": 100.0, "date": "2025-01-15"}
        with patch(
            "app.services.income.IncomeService.create",
            new_callable=AsyncMock,
            side_effect=RuntimeError("unexpected db error"),
        ):
            response = client.post(
                f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
                json=payload,
                headers=INTERNAL_HEADERS,
            )

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /internal/incomes/account/{account_id} (Get incomes by account)
# ---------------------------------------------------------------------------
class TestInternalGetIncomesByAccount:
    def test_get_by_account_empty(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/account/999?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_by_account_after_create(self, client: TestClient):
        # First create an income with an account
        with patch(
            "app.clients.account_service_client.AccountServiceClient.validate_account",
            new_callable=AsyncMock,
            return_value={"account": {"id": 42}},
        ), patch(
            "app.clients.account_service_client.AccountServiceClient.update_account_balance",
            new_callable=AsyncMock,
            return_value={"account": {"id": 42, "balance": 500.0}},
        ):
            create_resp = client.post(
                f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
                json={"amount": 500.0, "account_id": 42, "currency": "USD", "date": "2025-01-15"},
                headers=INTERNAL_HEADERS,
            )
            assert create_resp.status_code == 200

        response = client.get(
            f"/internal/incomes/account/42?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["account_id"] == 42

    def test_get_by_account_without_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/account/1?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
        )
        assert response.status_code == 403

    def test_get_by_account_with_pagination(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/account/1?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}&limit=5&offset=0",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /internal/incomes/account/{account_id}/validate (Validate account)
# ---------------------------------------------------------------------------
class TestInternalValidateAccount:
    def test_validate_account_success(self, client: TestClient):
        with patch(
            "app.clients.account_service_client.AccountServiceClient.validate_account",
            new_callable=AsyncMock,
            return_value={"account": {"id": 5, "currency": "USD"}},
        ):
            response = client.get(
                f"/internal/incomes/account/5/validate?user_id={TEST_USER_ID}",
                headers=INTERNAL_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["account_id"] == 5

    def test_validate_account_not_found(self, client: TestClient):
        with patch(
            "app.clients.account_service_client.AccountServiceClient.validate_account",
            new_callable=AsyncMock,
            side_effect=Exception("Account not found"),
        ):
            response = client.get(
                f"/internal/incomes/account/999/validate?user_id={TEST_USER_ID}",
                headers=INTERNAL_HEADERS,
            )

        assert response.status_code == 404

    def test_validate_account_without_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/account/5/validate?user_id={TEST_USER_ID}",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /internal/incomes/ai-summary (AI Summary)
# ---------------------------------------------------------------------------
class TestInternalAiSummary:
    def test_ai_summary_empty(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/ai-summary?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_ai_summary_with_data(self, client: TestClient):
        # Create an income first
        client.post(
            f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            json={"amount": 1000.0, "currency": "USD", "category_id": 1, "date": "2025-01-15"},
            headers=INTERNAL_HEADERS,
        )

        response = client.get(
            f"/internal/incomes/ai-summary?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        # May or may not contain the income depending on date (3 months window)
        assert "items" in data

    def test_ai_summary_without_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/incomes/ai-summary?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
        )
        assert response.status_code == 403

    def test_ai_summary_item_format(self, client: TestClient):
        """Items should have amount, category_id, currency, date fields."""
        # Create a recent income
        recent_date = datetime.utcnow().strftime("%Y-%m-%d")
        client.post(
            f"/internal/?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            json={"amount": 750.0, "currency": "EUR", "category_id": 3, "date": recent_date},
            headers=INTERNAL_HEADERS,
        )

        response = client.get(
            f"/internal/incomes/ai-summary?user_id={TEST_USER_ID}&workspace_id={TEST_WORKSPACE_ID}",
            headers=INTERNAL_HEADERS,
        )

        assert response.status_code == 200
        items = response.json()["items"]
        if items:
            item = items[0]
            assert "amount" in item
            assert "category_id" in item
            assert "currency" in item
            assert "date" in item
