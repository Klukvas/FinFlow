"""
Unit tests for custom exception classes.

Tests cover:
- All exception types instantiate correctly
- Error codes are set properly
- Exception messages are descriptive
- Exception hierarchy is correct
"""
import pytest

from app.exceptions import (
    DebtServiceException,
    DebtNotFoundError,
    ContactNotFoundError,
    PaymentNotFoundError,
    DebtValidationError,
    ContactValidationError,
    PaymentValidationError,
    DebtAmountError,
    PaymentAmountError,
    DebtDateError,
    ExternalServiceError,
    DatabaseError,
    ContactHasAssociatedDebtsError,
    DebtCreationFailedError,
    DebtUpdateFailedError,
    DebtDeletionFailedError,
    ContactCreationFailedError,
    ContactUpdateFailedError,
    ContactDeletionFailedError,
    PaymentCreationFailedError,
    InvalidDebtTypeError,
    InvalidPaymentMethodError,
    DebtLimitExceededError,
    DebtReadOnlyExcessError,
)


class TestDebtServiceException:
    """Tests for base DebtServiceException."""

    def test_base_exception(self):
        """Base exception stores message, code, and details."""
        exc = DebtServiceException("test error", "TEST_CODE", {"key": "value"})

        assert exc.message == "test error"
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"key": "value"}
        assert str(exc) == "test error"

    def test_base_exception_default_details(self):
        """Details default to empty dict."""
        exc = DebtServiceException("error", "CODE")

        assert exc.details == {}


class TestNotFoundErrors:
    """Tests for *NotFoundError exceptions."""

    def test_debt_not_found(self):
        """DebtNotFoundError has correct message and code."""
        exc = DebtNotFoundError(42)

        assert exc.debt_id == 42
        assert "42" in exc.message
        assert exc.error_code == "DEBT_NOT_FOUND"
        assert isinstance(exc, DebtServiceException)

    def test_contact_not_found(self):
        """ContactNotFoundError has correct message and code."""
        exc = ContactNotFoundError(7)

        assert exc.contact_id == 7
        assert "7" in exc.message
        assert exc.error_code == "CONTACT_NOT_FOUND"

    def test_payment_not_found(self):
        """PaymentNotFoundError has correct message and code."""
        exc = PaymentNotFoundError(15)

        assert exc.payment_id == 15
        assert "15" in exc.message
        assert exc.error_code == "PAYMENT_NOT_FOUND"


class TestValidationErrors:
    """Tests for validation error exceptions."""

    def test_debt_validation_error(self):
        """DebtValidationError carries custom message."""
        exc = DebtValidationError("Name is required")

        assert exc.message == "Name is required"
        assert exc.error_code == "DEBT_VALIDATION_FAILED"

    def test_contact_validation_error(self):
        """ContactValidationError carries custom message."""
        exc = ContactValidationError("Invalid email")

        assert exc.message == "Invalid email"
        assert exc.error_code == "CONTACT_VALIDATION_FAILED"

    def test_payment_validation_error(self):
        """PaymentValidationError carries custom message."""
        exc = PaymentValidationError("Amount too small")

        assert exc.message == "Amount too small"
        assert exc.error_code == "PAYMENT_VALIDATION_FAILED"

    def test_debt_amount_error(self):
        """DebtAmountError stores amount and max."""
        exc = DebtAmountError(1500000.0, 999999.99)

        assert exc.amount == 1500000.0
        assert exc.max_amount == 999999.99
        assert exc.error_code == "INVALID_DEBT_AMOUNT"

    def test_payment_amount_error(self):
        """PaymentAmountError stores amount and balance."""
        exc = PaymentAmountError(5000.0, 3000.0)

        assert exc.amount == 5000.0
        assert exc.remaining_balance == 3000.0
        assert exc.error_code == "PAYMENT_AMOUNT_EXCEEDS_BALANCE"

    def test_debt_date_error(self):
        """DebtDateError includes date info in message."""
        exc = DebtDateError("due_date before start_date")

        assert "due_date before start_date" in exc.message
        assert exc.error_code == "INVALID_DEBT_DATE"


class TestBusinessRuleErrors:
    """Tests for business rule violation exceptions."""

    def test_contact_has_debts_error(self):
        """ContactHasAssociatedDebtsError stores counts."""
        exc = ContactHasAssociatedDebtsError(5, 3)

        assert exc.contact_id == 5
        assert exc.debt_count == 3
        assert "3" in exc.message
        assert exc.error_code == "CONTACT_HAS_ASSOCIATED_DEBTS"

    def test_invalid_debt_type_error(self):
        """InvalidDebtTypeError stores the type."""
        exc = InvalidDebtTypeError("FANTASY")

        assert exc.debt_type == "FANTASY"
        assert exc.error_code == "INVALID_DEBT_TYPE"

    def test_invalid_payment_method_error(self):
        """InvalidPaymentMethodError stores the method."""
        exc = InvalidPaymentMethodError("BITCOIN")

        assert exc.payment_method == "BITCOIN"
        assert exc.error_code == "INVALID_PAYMENT_METHOD"

    def test_debt_limit_exceeded_error(self):
        """DebtLimitExceededError inherits from DebtValidationError."""
        exc = DebtLimitExceededError(10, 5)

        assert isinstance(exc, DebtValidationError)
        assert "10" in exc.message
        assert "5" in exc.message

    def test_debt_read_only_excess_error(self):
        """DebtReadOnlyExcessError stores context."""
        exc = DebtReadOnlyExcessError(42, 10, 5)

        assert exc.debt_id == 42
        assert exc.current_count == 10
        assert exc.limit == 5
        assert exc.error_code == "RECORD_READ_ONLY_EXCESS"


class TestOperationFailedErrors:
    """Tests for operation failure exceptions."""

    def test_debt_creation_failed(self):
        """DebtCreationFailedError has default message."""
        exc = DebtCreationFailedError()

        assert exc.message == "Failed to create debt"
        assert exc.error_code == "DEBT_CREATION_FAILED"

    def test_debt_creation_failed_custom_message(self):
        """DebtCreationFailedError accepts custom message."""
        exc = DebtCreationFailedError("Custom error")

        assert exc.message == "Custom error"

    def test_debt_update_failed(self):
        """DebtUpdateFailedError has correct code."""
        exc = DebtUpdateFailedError()

        assert exc.error_code == "DEBT_UPDATE_FAILED"

    def test_debt_deletion_failed(self):
        """DebtDeletionFailedError has correct code."""
        exc = DebtDeletionFailedError()

        assert exc.error_code == "DEBT_DELETION_FAILED"

    def test_contact_creation_failed(self):
        """ContactCreationFailedError has correct code."""
        exc = ContactCreationFailedError()

        assert exc.error_code == "CONTACT_CREATION_FAILED"

    def test_contact_update_failed(self):
        """ContactUpdateFailedError has correct code."""
        exc = ContactUpdateFailedError()

        assert exc.error_code == "CONTACT_UPDATE_FAILED"

    def test_contact_deletion_failed(self):
        """ContactDeletionFailedError has correct code."""
        exc = ContactDeletionFailedError()

        assert exc.error_code == "CONTACT_DELETION_FAILED"

    def test_payment_creation_failed(self):
        """PaymentCreationFailedError has correct code."""
        exc = PaymentCreationFailedError()

        assert exc.error_code == "PAYMENT_CREATION_FAILED"


class TestInfrastructureErrors:
    """Tests for infrastructure error exceptions."""

    def test_external_service_error(self):
        """ExternalServiceError stores service name."""
        exc = ExternalServiceError("category_service", "Connection refused")

        assert exc.service_name == "category_service"
        assert "category_service" in exc.message
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_database_error(self):
        """DatabaseError stores operation."""
        exc = DatabaseError("Constraint violation", "insert")

        assert exc.operation == "insert"
        assert "insert" in exc.message
        assert exc.error_code == "DATABASE_ERROR"


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_inherit_from_base(self):
        """All custom exceptions inherit from DebtServiceException."""
        exceptions = [
            DebtNotFoundError(1),
            ContactNotFoundError(1),
            PaymentNotFoundError(1),
            DebtValidationError("msg"),
            ContactValidationError("msg"),
            PaymentValidationError("msg"),
            DebtAmountError(1.0),
            PaymentAmountError(1.0, 1.0),
            DebtDateError("msg"),
            ExternalServiceError("svc", "msg"),
            DatabaseError("msg", "op"),
            ContactHasAssociatedDebtsError(1, 1),
            DebtCreationFailedError(),
            DebtUpdateFailedError(),
            DebtDeletionFailedError(),
            ContactCreationFailedError(),
            ContactUpdateFailedError(),
            ContactDeletionFailedError(),
            PaymentCreationFailedError(),
            InvalidDebtTypeError("LOAN"),
            InvalidPaymentMethodError("CASH"),
            DebtLimitExceededError(1, 1),
            DebtReadOnlyExcessError(1, 1, 1),
        ]

        for exc in exceptions:
            assert isinstance(exc, DebtServiceException), f"{type(exc).__name__} should inherit from DebtServiceException"
            assert isinstance(exc, Exception)

    def test_debt_limit_exceeded_is_validation_error(self):
        """DebtLimitExceededError inherits from DebtValidationError."""
        exc = DebtLimitExceededError(5, 3)

        assert isinstance(exc, DebtValidationError)
        assert isinstance(exc, DebtServiceException)
