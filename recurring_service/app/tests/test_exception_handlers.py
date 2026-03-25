"""Tests for exception handler functions."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.requests import Request

from app.exception_handlers import (
    base_recurring_error_handler,
    recurring_payment_not_found_handler,
    invalid_schedule_config_handler,
    payment_execution_error_handler,
    category_not_found_handler,
    validation_error_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.exceptions import (
    BaseRecurringError,
    RecurringPaymentNotFoundError,
    InvalidScheduleConfigError,
    PaymentExecutionError,
    CategoryNotFoundError,
    InvalidPaymentStatusError,
    PaymentAlreadyPausedError,
    PaymentNotPausedError,
    ScheduleNotFoundError,
    InvalidScheduleStatusError,
    ServiceClientError,
    DatabaseError,
    ValidationError,
    InternalServerError,
    RecurringReadOnlyExcessError,
)


@pytest.fixture
def mock_request():
    return MagicMock(spec=Request)


class TestBaseRecurringErrorHandler:
    @pytest.mark.asyncio
    async def test_not_found_errors_return_404(self, mock_request):
        exc = RecurringPaymentNotFoundError("not found")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_schedule_not_found_returns_404(self, mock_request):
        exc = ScheduleNotFoundError("schedule missing")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_schedule_config_returns_400(self, mock_request):
        exc = InvalidScheduleConfigError("bad config")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_category_not_found_returns_400(self, mock_request):
        exc = CategoryNotFoundError("category missing")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_payment_status_returns_400(self, mock_request):
        exc = InvalidPaymentStatusError("bad status")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_payment_already_paused_returns_400(self, mock_request):
        exc = PaymentAlreadyPausedError()
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_payment_not_paused_returns_400(self, mock_request):
        exc = PaymentNotPausedError()
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_schedule_status_returns_400(self, mock_request):
        exc = InvalidScheduleStatusError()
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_error_returns_400(self, mock_request):
        exc = ValidationError("invalid data")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_read_only_excess_returns_403(self, mock_request):
        exc = RecurringReadOnlyExcessError("pay-1", 10, 5)
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_payment_execution_error_returns_500(self, mock_request):
        exc = PaymentExecutionError("execution failed")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_service_client_error_returns_500(self, mock_request):
        exc = ServiceClientError("client error")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_database_error_returns_500(self, mock_request):
        exc = DatabaseError("db error")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_internal_server_error_returns_500(self, mock_request):
        exc = InternalServerError("server error")
        response = await base_recurring_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_response_body_contains_error_and_code(self, mock_request):
        exc = RecurringPaymentNotFoundError("Payment 99 not found")
        response = await base_recurring_error_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "Payment 99 not found"
        assert body["errorCode"] == "RECURRING_PAYMENT_NOT_FOUND"


class TestSpecificHandlers:
    @pytest.mark.asyncio
    async def test_recurring_payment_not_found_handler(self, mock_request):
        exc = RecurringPaymentNotFoundError("not found")
        response = await recurring_payment_not_found_handler(mock_request, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_schedule_config_handler(self, mock_request):
        exc = InvalidScheduleConfigError("bad config")
        response = await invalid_schedule_config_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_payment_execution_error_handler(self, mock_request):
        exc = PaymentExecutionError("failed")
        response = await payment_execution_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_category_not_found_handler(self, mock_request):
        exc = CategoryNotFoundError("no category")
        response = await category_not_found_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, mock_request):
        exc = ValidationError("invalid")
        response = await validation_error_handler(mock_request, exc)
        assert response.status_code == 400


class TestHttpExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_http_exception(self, mock_request):
        exc = HTTPException(status_code=422, detail="Unprocessable")
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 422
        import json
        body = json.loads(response.body)
        assert body["error"] == "Unprocessable"
        assert body["errorCode"] == "HTTP_EXCEPTION"

    @pytest.mark.asyncio
    async def test_handles_404_http_exception(self, mock_request):
        exc = HTTPException(status_code=404, detail="Not Found")
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 404


class TestGeneralExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_generic_exception(self, mock_request):
        exc = RuntimeError("unexpected error")
        response = await general_exception_handler(mock_request, exc)
        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"] == "Internal server error"
        assert body["errorCode"] == "INTERNAL_SERVER_ERROR"

    @pytest.mark.asyncio
    async def test_does_not_leak_error_details(self, mock_request):
        exc = RuntimeError("sensitive database info")
        response = await general_exception_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert "sensitive" not in body["error"]
