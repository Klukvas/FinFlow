"""Tests for app/exceptions/bank_sync_exceptions.py - all custom exceptions."""

import pytest

from app.exceptions import (
    BankSyncException,
    ConnectionNotFoundError,
    LinkedAccountNotFoundError,
    SyncLogNotFoundError,
    TokenValidationError,
    MonobankApiError,
    RateLimitError,
    EncryptionError,
    SyncInProgressError,
    AccountNotLinkedError,
    ExternalServiceError,
    TransactionLimitExceededError,
    DatabaseError,
)


class TestBankSyncException:
    def test_base_exception_attributes(self):
        exc = BankSyncException("test error", "TEST_CODE", {"key": "val"})
        assert exc.message == "test error"
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"key": "val"}
        assert str(exc) == "test error"

    def test_base_exception_default_details(self):
        exc = BankSyncException("msg", "CODE")
        assert exc.details == {}


class TestConnectionNotFoundError:
    def test_message_contains_connection_id(self):
        exc = ConnectionNotFoundError(42)
        assert "42" in exc.message
        assert exc.error_code == "CONNECTION_NOT_FOUND"

    def test_is_bank_sync_exception(self):
        assert issubclass(ConnectionNotFoundError, BankSyncException)


class TestLinkedAccountNotFoundError:
    def test_message_contains_account_id(self):
        exc = LinkedAccountNotFoundError(99)
        assert "99" in exc.message
        assert exc.error_code == "LINKED_ACCOUNT_NOT_FOUND"


class TestSyncLogNotFoundError:
    def test_message_contains_sync_log_id(self):
        exc = SyncLogNotFoundError(7)
        assert "7" in exc.message
        assert exc.error_code == "SYNC_LOG_NOT_FOUND"


class TestTokenValidationError:
    def test_default_message(self):
        exc = TokenValidationError()
        assert "Invalid Monobank token" in exc.message
        assert exc.error_code == "TOKEN_VALIDATION_FAILED"

    def test_custom_message(self):
        exc = TokenValidationError("Custom validation message")
        assert exc.message == "Custom validation message"


class TestMonobankApiError:
    def test_default_message(self):
        exc = MonobankApiError()
        assert "Monobank API error" in exc.message
        assert exc.error_code == "MONOBANK_API_ERROR"

    def test_custom_message(self):
        exc = MonobankApiError("API is down")
        assert exc.message == "API is down"


class TestRateLimitError:
    def test_contains_seconds_remaining(self):
        exc = RateLimitError(30)
        assert "30" in exc.message
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.details["seconds_remaining"] == 30


class TestEncryptionError:
    def test_default_message(self):
        exc = EncryptionError()
        assert "encryption" in exc.message.lower() or "decryption" in exc.message.lower()
        assert exc.error_code == "ENCRYPTION_ERROR"


class TestSyncInProgressError:
    def test_message_contains_connection_id(self):
        exc = SyncInProgressError(5)
        assert "5" in exc.message
        assert exc.error_code == "SYNC_IN_PROGRESS"


class TestAccountNotLinkedError:
    def test_message_contains_account_id(self):
        exc = AccountNotLinkedError(10)
        assert "10" in exc.message
        assert exc.error_code == "ACCOUNT_NOT_LINKED"


class TestExternalServiceError:
    def test_message_contains_service_name(self):
        exc = ExternalServiceError("expense_service", "timeout")
        assert "expense_service" in exc.message
        assert "timeout" in exc.message
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"


class TestTransactionLimitExceededError:
    def test_stores_transaction_type(self):
        exc = TransactionLimitExceededError("expense")
        assert exc.transaction_type == "expense"
        assert exc.error_code == "TRANSACTION_LIMIT_EXCEEDED"
        assert exc.details["transaction_type"] == "expense"

    def test_custom_message(self):
        exc = TransactionLimitExceededError("income", "Plan limit reached")
        assert exc.message == "Plan limit reached"

    def test_default_message(self):
        exc = TransactionLimitExceededError("expense")
        assert "expense" in exc.message


class TestDatabaseError:
    def test_with_operation(self):
        exc = DatabaseError("connection refused", "insert")
        assert "insert" in exc.message
        assert "connection refused" in exc.message
        assert exc.error_code == "DATABASE_ERROR"

    def test_without_operation(self):
        exc = DatabaseError("connection refused")
        assert "connection refused" in exc.message
