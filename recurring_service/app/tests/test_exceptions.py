"""Tests for all exception classes in recurring_exceptions.py"""
import pytest

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
    RecurringLimitExceededError,
    RecurringReadOnlyExcessError,
)


class TestBaseRecurringError:
    def test_stores_message_and_error_code(self):
        exc = BaseRecurringError("something went wrong", "CUSTOM_CODE")
        assert exc.message == "something went wrong"
        assert exc.error_code == "CUSTOM_CODE"
        assert str(exc) == "something went wrong"

    def test_is_exception_subclass(self):
        exc = BaseRecurringError("msg", "CODE")
        assert isinstance(exc, Exception)


class TestRecurringPaymentNotFoundError:
    def test_default_message(self):
        exc = RecurringPaymentNotFoundError()
        assert exc.message == "Recurring payment not found"
        assert exc.error_code == "RECURRING_PAYMENT_NOT_FOUND"

    def test_custom_message(self):
        exc = RecurringPaymentNotFoundError("Payment 123 not found")
        assert exc.message == "Payment 123 not found"
        assert exc.error_code == "RECURRING_PAYMENT_NOT_FOUND"

    def test_inherits_base(self):
        exc = RecurringPaymentNotFoundError()
        assert isinstance(exc, BaseRecurringError)


class TestInvalidScheduleConfigError:
    def test_default_message(self):
        exc = InvalidScheduleConfigError()
        assert exc.message == "Invalid schedule configuration"
        assert exc.error_code == "INVALID_SCHEDULE_CONFIG"

    def test_custom_message(self):
        exc = InvalidScheduleConfigError("Missing day_of_week")
        assert exc.message == "Missing day_of_week"


class TestPaymentExecutionError:
    def test_default_message(self):
        exc = PaymentExecutionError()
        assert exc.message == "Payment execution failed"
        assert exc.error_code == "PAYMENT_EXECUTION_FAILED"

    def test_custom_message(self):
        exc = PaymentExecutionError("Timeout calling expense service")
        assert exc.message == "Timeout calling expense service"


class TestCategoryNotFoundError:
    def test_default_message(self):
        exc = CategoryNotFoundError()
        assert exc.message == "Category not found"
        assert exc.error_code == "CATEGORY_NOT_FOUND"

    def test_custom_message(self):
        exc = CategoryNotFoundError("Category 42 not found")
        assert exc.message == "Category 42 not found"


class TestInvalidPaymentStatusError:
    def test_default_message(self):
        exc = InvalidPaymentStatusError()
        assert exc.message == "Invalid payment status"
        assert exc.error_code == "INVALID_PAYMENT_STATUS"


class TestPaymentAlreadyPausedError:
    def test_default_message(self):
        exc = PaymentAlreadyPausedError()
        assert exc.message == "Payment is already paused"
        assert exc.error_code == "PAYMENT_ALREADY_PAUSED"


class TestPaymentNotPausedError:
    def test_default_message(self):
        exc = PaymentNotPausedError()
        assert exc.message == "Payment is not paused"
        assert exc.error_code == "PAYMENT_NOT_PAUSED"


class TestScheduleNotFoundError:
    def test_default_message(self):
        exc = ScheduleNotFoundError()
        assert exc.message == "Payment schedule not found"
        assert exc.error_code == "SCHEDULE_NOT_FOUND"


class TestInvalidScheduleStatusError:
    def test_default_message(self):
        exc = InvalidScheduleStatusError()
        assert exc.message == "Invalid schedule status"
        assert exc.error_code == "INVALID_SCHEDULE_STATUS"


class TestServiceClientError:
    def test_default_message(self):
        exc = ServiceClientError()
        assert exc.message == "External service client error"
        assert exc.error_code == "SERVICE_CLIENT_ERROR"


class TestDatabaseError:
    def test_default_message(self):
        exc = DatabaseError()
        assert exc.message == "Database operation failed"
        assert exc.error_code == "DATABASE_ERROR"


class TestValidationError:
    def test_default_message(self):
        exc = ValidationError()
        assert exc.message == "Validation failed"
        assert exc.error_code == "VALIDATION_ERROR"


class TestInternalServerError:
    def test_default_message(self):
        exc = InternalServerError()
        assert exc.message == "Internal server error"
        assert exc.error_code == "INTERNAL_SERVER_ERROR"


class TestRecurringLimitExceededError:
    def test_message_includes_counts(self):
        exc = RecurringLimitExceededError(current_count=5, limit=3)
        assert "5" in exc.message
        assert "3" in exc.message
        assert exc.error_code == "RECURRING_LIMIT_EXCEEDED"

    def test_inherits_base(self):
        exc = RecurringLimitExceededError(current_count=1, limit=1)
        assert isinstance(exc, BaseRecurringError)


class TestRecurringReadOnlyExcessError:
    def test_message_includes_counts(self):
        exc = RecurringReadOnlyExcessError(payment_id="pay-1", current_count=10, limit=5)
        assert "10" in exc.message
        assert "5" in exc.message
        assert exc.error_code == "RECORD_READ_ONLY_EXCESS"

    def test_stores_payment_id_and_counts(self):
        exc = RecurringReadOnlyExcessError(payment_id="pay-2", current_count=8, limit=3)
        assert exc.payment_id == "pay-2"
        assert exc.current_count == 8
        assert exc.limit == 3

    def test_inherits_base(self):
        exc = RecurringReadOnlyExcessError(payment_id="x", current_count=1, limit=1)
        assert isinstance(exc, BaseRecurringError)
