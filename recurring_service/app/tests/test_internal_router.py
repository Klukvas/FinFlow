"""Tests for internal API endpoints."""
import pytest
from datetime import date
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4


class TestExecuteRecurringPaymentsEndpoint:
    def test_execute_payments(self, internal_client):
        with patch(
            "app.routers.internal.executor.execute_pending_payments",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {"succeeded": 3, "failed": 1}
            response = internal_client.post("/internal/execute-recurring-payments")
            assert response.status_code == 200
            data = response.json()
            assert data["succeeded"] == 3
            assert data["failed"] == 1

    def test_execute_payments_with_date(self, internal_client):
        with patch(
            "app.routers.internal.executor.execute_pending_payments",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {"succeeded": 0, "failed": 0}
            response = internal_client.post(
                "/internal/execute-recurring-payments?execution_date=2025-01-15"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["succeeded"] == 0

    def test_execute_payments_no_results(self, internal_client):
        with patch(
            "app.routers.internal.executor.execute_pending_payments",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {"succeeded": 0, "failed": 0}
            response = internal_client.post("/internal/execute-recurring-payments")
            assert response.status_code == 200


class TestGetPendingPaymentsEndpoint:
    def test_get_pending_payments_empty(self, internal_client, db_session):
        response = internal_client.get("/internal/pending-payments")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["payments"] == []

    def test_get_pending_payments_with_date(self, internal_client, db_session):
        response = internal_client.get(
            "/internal/pending-payments?execution_date=2025-01-15"
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "execution_date" in data

    def test_get_pending_payments_returns_due_payments(
        self, internal_client, created_recurring_payment
    ):
        # The payment has next_execution=2025-01-15, so querying on that date should find it
        response = internal_client.get(
            "/internal/pending-payments?execution_date=2025-01-15"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestRetryFailedPaymentEndpoint:
    def test_retry_success(self, internal_client):
        schedule_id = str(uuid4())
        with patch(
            "app.routers.internal.executor.retry_failed_payment",
            new_callable=AsyncMock,
        ) as mock_retry:
            mock_retry.return_value = True
            response = internal_client.post(
                f"/internal/retry-failed-payment/{schedule_id}"
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Payment retry successful"

    def test_retry_failure_raises(self, internal_client):
        schedule_id = str(uuid4())
        with patch(
            "app.routers.internal.executor.retry_failed_payment",
            new_callable=AsyncMock,
        ) as mock_retry:
            mock_retry.return_value = False
            response = internal_client.post(
                f"/internal/retry-failed-payment/{schedule_id}"
            )
            # Should return error since retry returned False
            assert response.status_code in (404, 500)


class TestSchedulerStatusEndpoint:
    def test_get_scheduler_status(self, internal_client):
        with patch(
            "app.routers.internal.scheduler_service.get_scheduler_status",
        ) as mock_status:
            mock_status.return_value = {
                "running": True,
                "jobs": [
                    {
                        "id": "execute_recurring_payments",
                        "name": "Execute Recurring Payments",
                        "next_run_time": "2025-01-16T00:01:00",
                        "trigger": "cron[hour='0', minute='1']",
                    }
                ],
            }
            response = internal_client.get("/internal/scheduler/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["scheduler"]["running"] is True


class TestExecuteNowEndpoint:
    def test_execute_now(self, internal_client):
        with patch(
            "app.routers.internal.scheduler_service.execute_now",
        ) as mock_exec:
            mock_exec.return_value = None
            response = internal_client.post("/internal/scheduler/execute-now")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Manual execution triggered" in data["message"]


class TestRecurringAiSummaryEndpoint:
    def test_get_ai_summary_empty(self, internal_client, db_session):
        response = internal_client.get(
            "/internal/recurring/ai-summary?user_id=1&workspace_id=550e8400-e29b-41d4-a716-446655440000"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_get_ai_summary_with_payments(
        self, internal_client, created_recurring_payment
    ):
        workspace_id = str(created_recurring_payment.workspace_id)
        user_id = created_recurring_payment.user_id
        response = internal_client.get(
            f"/internal/recurring/ai-summary?user_id={user_id}&workspace_id={workspace_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert "name" in item
        assert "amount" in item
        assert "payment_type" in item

    def test_get_ai_summary_requires_user_id(self, internal_client):
        response = internal_client.get(
            "/internal/recurring/ai-summary?workspace_id=550e8400-e29b-41d4-a716-446655440000"
        )
        assert response.status_code == 422

    def test_get_ai_summary_requires_workspace_id(self, internal_client):
        response = internal_client.get(
            "/internal/recurring/ai-summary?user_id=1"
        )
        assert response.status_code == 422


class TestHealthCheckEndpoint:
    def test_health_check(self, internal_client):
        response = internal_client.get("/internal/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "recurring-payments"
