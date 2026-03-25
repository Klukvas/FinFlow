"""Tests for recurring payments API endpoints."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, AsyncMock
from uuid import UUID, uuid4

TEST_USER_ID = 1
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def _make_mock_payment(**overrides):
    """Create a mock RecurringPayment model object."""
    from app.models.recurring_payment import RecurringPayment

    defaults = {
        "id": uuid4(),
        "user_id": TEST_USER_ID,
        "workspace_id": TEST_WORKSPACE_ID,
        "name": "Test Payment",
        "description": None,
        "amount": Decimal("100.00"),
        "currency": "USD",
        "category_id": 1,
        "payment_type": "EXPENSE",
        "schedule_type": "daily",
        "schedule_config": {},
        "start_date": date(2025, 1, 1),
        "end_date": None,
        "status": "active",
        "last_executed": None,
        "next_execution": date(2025, 1, 1),
        "created_at": date(2025, 1, 1),
        "updated_at": date(2025, 1, 1),
        "is_read_only": False,
    }
    defaults.update(overrides)
    payment = RecurringPayment()
    for k, v in defaults.items():
        setattr(payment, k, v)
    return payment


class TestCreateRecurringPaymentEndpoint:
    def test_create_monthly_expense(self, client, sample_recurring_payment_data):
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.create_recurring_payment",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_payment = _make_mock_payment(
                name=sample_recurring_payment_data["name"],
                description=sample_recurring_payment_data["description"],
                amount=Decimal(sample_recurring_payment_data["amount"]),
                currency=sample_recurring_payment_data["currency"],
                category_id=sample_recurring_payment_data["category_id"],
                payment_type=sample_recurring_payment_data["payment_type"],
                schedule_type=sample_recurring_payment_data["schedule_type"],
                schedule_config=sample_recurring_payment_data["schedule_config"],
            )
            mock_create.return_value = mock_payment

            response = client.post(
                "/recurring-payments/",
                json=sample_recurring_payment_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Monthly Rent"
            assert data["payment_type"] == "EXPENSE"

    def test_create_with_invalid_data_returns_422(self, client):
        response = client.post(
            "/recurring-payments/",
            json={"name": ""},
        )
        assert response.status_code == 422


class TestGetRecurringPaymentsEndpoint:
    def test_get_empty_list(self, client):
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_recurring_payments",
        ) as mock_get, patch(
            "app.services.recurring_payment_service.RecurringPaymentService._get_ordered_ids",
            return_value=[],
        ):
            from app.schemas.recurring_payment import RecurringPaymentListResponse

            mock_get.return_value = RecurringPaymentListResponse(
                items=[], total=0, page=1, size=50, pages=0
            )
            response = client.get("/recurring-payments/")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["items"] == []

    def test_get_with_status_filter(self, client):
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_recurring_payments",
        ) as mock_get, patch(
            "app.services.recurring_payment_service.RecurringPaymentService._get_ordered_ids",
            return_value=[],
        ):
            from app.schemas.recurring_payment import RecurringPaymentListResponse

            mock_get.return_value = RecurringPaymentListResponse(
                items=[], total=0, page=1, size=50, pages=0
            )
            response = client.get("/recurring-payments/?status=active")
            assert response.status_code == 200

    def test_get_with_pagination(self, client):
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_recurring_payments",
        ) as mock_get, patch(
            "app.services.recurring_payment_service.RecurringPaymentService._get_ordered_ids",
            return_value=[],
        ):
            from app.schemas.recurring_payment import RecurringPaymentListResponse

            mock_get.return_value = RecurringPaymentListResponse(
                items=[], total=0, page=2, size=10, pages=0
            )
            response = client.get("/recurring-payments/?page=2&size=10")
            assert response.status_code == 200


class TestGetRecurringPaymentEndpoint:
    def test_get_by_id(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_recurring_payment",
        ) as mock_get:
            mock_payment = _make_mock_payment(id=payment_id)
            mock_get.return_value = mock_payment

            response = client.get(f"/recurring-payments/{payment_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(payment_id)

    def test_get_invalid_uuid_returns_422(self, client):
        response = client.get("/recurring-payments/not-a-uuid")
        assert response.status_code == 422


class TestUpdateRecurringPaymentEndpoint:
    def test_update_payment(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.update_recurring_payment",
            new_callable=AsyncMock,
        ) as mock_update:
            mock_payment = _make_mock_payment(
                id=payment_id,
                name="Updated Name",
                amount=Decimal("200.00"),
            )
            mock_update.return_value = mock_payment

            response = client.put(
                f"/recurring-payments/{payment_id}",
                json={"name": "Updated Name", "amount": "200.00"},
            )
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Name"


class TestDeleteRecurringPaymentEndpoint:
    def test_delete_payment(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.delete_recurring_payment",
        ) as mock_delete:
            mock_delete.return_value = None
            response = client.delete(f"/recurring-payments/{payment_id}")
            assert response.status_code == 204


class TestPauseRecurringPaymentEndpoint:
    def test_pause_payment(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.pause_recurring_payment",
        ) as mock_pause:
            mock_pause.return_value = None
            response = client.post(f"/recurring-payments/{payment_id}/pause")
            assert response.status_code == 200
            assert response.json()["message"] == "Recurring payment paused successfully"


class TestResumeRecurringPaymentEndpoint:
    def test_resume_payment(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.resume_recurring_payment",
        ) as mock_resume:
            mock_resume.return_value = None
            response = client.post(f"/recurring-payments/{payment_id}/resume")
            assert response.status_code == 200
            assert response.json()["message"] == "Recurring payment resumed successfully"


class TestGetPaymentSchedulesEndpoint:
    def test_get_schedules(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_payment_schedules",
        ) as mock_schedules:
            from app.schemas.payment_schedule import PaymentScheduleListResponse

            mock_schedules.return_value = PaymentScheduleListResponse(
                items=[], total=0, page=1, size=50, pages=0
            )
            response = client.get(f"/recurring-payments/{payment_id}/schedules")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0

    def test_get_schedules_with_filters(self, client):
        payment_id = uuid4()
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_payment_schedules",
        ) as mock_schedules:
            from app.schemas.payment_schedule import PaymentScheduleListResponse

            mock_schedules.return_value = PaymentScheduleListResponse(
                items=[], total=0, page=1, size=50, pages=0
            )
            response = client.get(
                f"/recurring-payments/{payment_id}/schedules?status=executed&page=1&size=10"
            )
            assert response.status_code == 200


class TestGetPaymentStatisticsEndpoint:
    def test_get_statistics(self, client):
        with patch(
            "app.services.recurring_payment_service.RecurringPaymentService.get_payment_statistics",
        ) as mock_stats:
            mock_stats.return_value = {
                "total_payments": 5,
                "active_payments": 3,
                "paused_payments": 2,
                "executed_this_month": 10,
                "failed_this_month": 1,
            }
            response = client.get("/recurring-payments/statistics/summary")
            assert response.status_code == 200
            data = response.json()
            assert data["total_payments"] == 5
            assert data["active_payments"] == 3
