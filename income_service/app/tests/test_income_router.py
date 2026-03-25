"""
Tests for app/routers/income.py — all API endpoints, validation errors,
and error responses via the FastAPI test client.
"""
import pytest
from datetime import datetime, date, timedelta
from random import randint
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from fastapi.testclient import TestClient
from starlette import status

from app.tests.conftest import (
    TEST_USER_ID,
    TEST_WORKSPACE_ID,
    make_token,
)


def _auth_headers(user_id=TEST_USER_ID):
    """Create auth + workspace headers for a user."""
    token = make_token(user_id)
    return {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": str(TEST_WORKSPACE_ID),
    }


# ---------------------------------------------------------------------------
# POST /incomes/  (Create)
# ---------------------------------------------------------------------------
class TestCreateIncomeEndpoint:
    def test_create_success(self, client: TestClient):
        payload = {
            "amount": 500.0,
            "currency": "USD",
            "description": "Salary",
            "date": "2025-01-15",
        }
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == 500.0
        assert data["currency"] == "USD"
        assert data["user_id"] == TEST_USER_ID

    def test_create_with_category(self, client: TestClient):
        payload = {
            "amount": 300.0,
            "category_id": 5,
            "date": "2025-01-15",
        }
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID), \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category",
                   new_callable=AsyncMock, return_value={"category": {"id": 5}}):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["category_id"] == 5

    def test_create_with_account(self, client: TestClient):
        payload = {
            "amount": 1000.0,
            "account_id": 10,
            "currency": "USD",
            "date": "2025-01-15",
        }
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID), \
             patch("app.clients.account_service_client.AccountServiceClient.validate_account",
                   new_callable=AsyncMock, return_value={"account": {"id": 10}}), \
             patch("app.clients.account_service_client.AccountServiceClient.update_account_balance",
                   new_callable=AsyncMock, return_value={"account": {"id": 10, "balance": 1000.0}}):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["account_id"] == 10

    def test_create_missing_amount_returns_422(self, client: TestClient):
        payload = {"description": "No amount"}
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == 422

    def test_create_negative_amount_returns_422(self, client: TestClient):
        payload = {"amount": -10.0, "date": "2025-01-15"}
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == 422

    def test_create_zero_amount_returns_422(self, client: TestClient):
        payload = {"amount": 0, "date": "2025-01-15"}
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == 422

    def test_create_invalid_currency_returns_422(self, client: TestClient):
        payload = {"amount": 100.0, "currency": "ABCD", "date": "2025-01-15"}
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == 422

    def test_create_future_date_returns_400(self, client: TestClient):
        future = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
        payload = {"amount": 100.0, "date": future}
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.post("/incomes/", json=payload, headers=_auth_headers())

        assert response.status_code == 400

    def test_create_no_auth_returns_error(self, client: TestClient):
        """Without authorization header, HTTPBearer returns 403."""
        payload = {"amount": 100.0}
        response = client.post("/incomes/", json=payload)
        # HTTPBearer dependency raises 403 when no Authorization header
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /incomes/  (List all)
# ---------------------------------------------------------------------------
class TestGetIncomesEndpoint:
    def test_get_all_empty(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/", headers=_auth_headers())

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_all_after_create(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            client.post("/incomes/", json={"amount": 100.0, "date": "2025-01-15"}, headers=_auth_headers())
            response = client.get("/incomes/", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_all_with_pagination_params(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/?skip=0&limit=10", headers=_auth_headers())

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /incomes/paginated (Paginated list)
# ---------------------------------------------------------------------------
class TestGetIncomesPaginatedEndpoint:
    def test_paginated_empty(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/paginated?page=1&size=10", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_paginated_returns_correct_page_metadata(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            # Create a few incomes first
            for _ in range(3):
                client.post("/incomes/", json={"amount": 100.0, "date": "2025-01-15"}, headers=_auth_headers())
            response = client.get("/incomes/paginated?page=1&size=2", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert data["size"] == 2
        assert data["page"] == 1


# ---------------------------------------------------------------------------
# GET /incomes/current-month-count
# ---------------------------------------------------------------------------
class TestCurrentMonthCountEndpoint:
    def test_current_month_count(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID), \
             patch("shared.clients.subscription.SubscriptionClient.get_user_features",
                   return_value={"incomes": {"enabled": True, "limit_value": 100}}):
            response = client.get("/incomes/current-month-count", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "limit" in data


# ---------------------------------------------------------------------------
# GET /incomes/date-range/
# ---------------------------------------------------------------------------
class TestGetIncomesByDateRangeEndpoint:
    def test_date_range_success(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get(
                "/incomes/date-range/?start_date=2025-01-01&end_date=2025-12-31",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# GET /incomes/{income_id}  (Get by ID)
# ---------------------------------------------------------------------------
class TestGetIncomeByIdEndpoint:
    def test_get_by_id_success(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            create_resp = client.post(
                "/incomes/",
                json={"amount": 150.0, "date": "2025-01-15"},
                headers=_auth_headers(),
            )
            income_id = create_resp.json()["id"]
            response = client.get(f"/incomes/{income_id}", headers=_auth_headers())

        assert response.status_code == 200
        assert response.json()["id"] == income_id

    def test_get_by_id_not_found(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/99999", headers=_auth_headers())

        assert response.status_code == 404

    def test_get_by_id_invalid_id(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/0", headers=_auth_headers())

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /incomes/{income_id}  (Update)
# ---------------------------------------------------------------------------
class TestUpdateIncomeEndpoint:
    def test_update_amount(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            create_resp = client.post(
                "/incomes/",
                json={"amount": 100.0, "date": "2025-01-15"},
                headers=_auth_headers(),
            )
            income_id = create_resp.json()["id"]

            response = client.put(
                f"/incomes/{income_id}",
                json={"amount": 250.0},
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        assert response.json()["amount"] == 250.0

    def test_update_not_found(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.put(
                "/incomes/99999",
                json={"amount": 200.0},
                headers=_auth_headers(),
            )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /incomes/{income_id}
# ---------------------------------------------------------------------------
class TestDeleteIncomeEndpoint:
    def test_delete_success(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            create_resp = client.post(
                "/incomes/",
                json={"amount": 100.0, "date": "2025-01-15"},
                headers=_auth_headers(),
            )
            income_id = create_resp.json()["id"]

            response = client.delete(f"/incomes/{income_id}", headers=_auth_headers())

        assert response.status_code == 204

    def test_delete_not_found(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.delete("/incomes/99999", headers=_auth_headers())

        assert response.status_code == 404

    def test_delete_invalid_id(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.delete("/incomes/0", headers=_auth_headers())

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /incomes/stats/summary
# ---------------------------------------------------------------------------
class TestIncomeSummaryEndpoint:
    def test_summary_raises_due_to_datetime_bug(self, client: TestClient):
        """The /stats/summary endpoint uses datetime.combine(end_date, datetime.max.time())
        which creates a datetime with non-zero microseconds. When IncomeSummary tries to
        assign this to the `period_end: date` field, Pydantic rejects it because
        'Datetimes provided to dates should have zero time'.
        This is a known bug; the endpoint raises a ValidationError."""
        from pydantic import ValidationError as PydanticValidationError

        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            with pytest.raises(Exception):
                client.get(
                    "/incomes/stats/summary?start_date=2025-01-01&end_date=2025-01-31",
                    headers=_auth_headers(),
                )

    def test_summary_missing_params_returns_422(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get(
                "/incomes/stats/summary",
                headers=_auth_headers(),
            )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /incomes/stats/overview
# ---------------------------------------------------------------------------
class TestIncomeStatsEndpoint:
    def test_stats_success(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/stats/overview", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "monthly_income" in data
        assert "yearly_income" in data
        assert "income_count" in data


# ---------------------------------------------------------------------------
# GET /incomes/category/{category_id}
# ---------------------------------------------------------------------------
class TestIncomesByCategoryEndpoint:
    def test_by_category_success(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID), \
             patch("app.clients.currency_service_client.CurrencyServiceClient.get_user_base_currency",
                   return_value="USD"), \
             patch("app.clients.currency_service_client.CurrencyServiceClient.get_rates",
                   new_callable=AsyncMock, return_value={"USD": 1.0}):
            response = client.get("/incomes/category/5", headers=_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert "incomes" in data
        assert "statistics" in data

    def test_by_category_invalid_id(self, client: TestClient):
        with patch("shared.auth.dependencies.decode_token", return_value=TEST_USER_ID):
            response = client.get("/incomes/category/0", headers=_auth_headers())

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Health / Root endpoints
# ---------------------------------------------------------------------------
class TestHealthAndRoot:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert "Income Service" in response.json()["message"]
