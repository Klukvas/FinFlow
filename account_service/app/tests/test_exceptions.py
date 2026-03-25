"""
Tests for app/exceptions/account_errors.py — custom exception classes.
"""
import pytest

from app.exceptions import (
    AccountServiceError,
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    ExternalServiceError,
    AccountLimitExceededError,
    AccountReadOnlyExcessError,
    AccountErrorCode,
)


class TestAccountErrorCode:
    def test_all_codes_are_strings(self):
        for code in AccountErrorCode:
            assert isinstance(code.value, str)

    def test_expected_codes_exist(self):
        expected = [
            "ACCOUNT_NOT_FOUND",
            "ACCOUNT_NOT_OWNED",
            "ACCOUNT_ARCHIVED",
            "VALIDATION_ERROR",
            "INVALID_BALANCE",
            "INVALID_CURRENCY",
            "INVALID_ACCOUNT_NAME",
            "INVALID_ACCOUNT_DESCRIPTION",
            "EXTERNAL_SERVICE_ERROR",
            "INSUFFICIENT_FUNDS",
            "CURRENCY_CONVERSION_FAILED",
            "DATABASE_ERROR",
            "UNKNOWN_ERROR",
            "ACCOUNT_LIMIT_EXCEEDED",
        ]
        actual = [code.value for code in AccountErrorCode]
        for code in expected:
            assert code in actual


class TestAccountServiceError:
    def test_base_error_fields(self):
        err = AccountServiceError("test message", "TEST_CODE", "details")
        assert err.message == "test message"
        assert err.error_code == "TEST_CODE"
        assert err.details == "details"
        assert str(err) == "test message"

    def test_base_error_without_details(self):
        err = AccountServiceError("msg", "CODE")
        assert err.details is None


class TestAccountNotFoundError:
    def test_message_includes_id(self):
        err = AccountNotFoundError(42)
        assert err.account_id == 42
        assert "42" in err.message
        assert err.error_code == AccountErrorCode.ACCOUNT_NOT_FOUND

    def test_inherits_service_error(self):
        err = AccountNotFoundError(1)
        assert isinstance(err, AccountServiceError)


class TestAccountValidationError:
    def test_custom_message(self):
        err = AccountValidationError("bad input")
        assert err.message == "bad input"
        assert err.error_code == AccountErrorCode.VALIDATION_ERROR

    def test_custom_error_code(self):
        err = AccountValidationError("bad name", AccountErrorCode.INVALID_ACCOUNT_NAME)
        assert err.error_code == AccountErrorCode.INVALID_ACCOUNT_NAME


class TestAccountOwnershipError:
    def test_fields(self):
        err = AccountOwnershipError(10, 5)
        assert err.account_id == 10
        assert err.user_id == 5
        assert "5" in err.message
        assert "10" in err.message
        assert err.error_code == AccountErrorCode.ACCOUNT_NOT_OWNED


class TestAccountArchivedError:
    def test_fields(self):
        err = AccountArchivedError(7)
        assert err.account_id == 7
        assert "7" in err.message
        assert err.error_code == AccountErrorCode.ACCOUNT_ARCHIVED


class TestAccountBalanceError:
    def test_default_code(self):
        err = AccountBalanceError("invalid")
        assert err.error_code == AccountErrorCode.INVALID_BALANCE

    def test_custom_code(self):
        err = AccountBalanceError("no funds", AccountErrorCode.INSUFFICIENT_FUNDS)
        assert err.error_code == AccountErrorCode.INSUFFICIENT_FUNDS


class TestExternalServiceError:
    def test_fields(self):
        err = ExternalServiceError("expense-service", "connection refused")
        assert err.service == "expense-service"
        assert err.error_code == AccountErrorCode.EXTERNAL_SERVICE_ERROR
        assert "expense-service" in err.message


class TestAccountLimitExceededError:
    def test_message(self):
        err = AccountLimitExceededError(5, 5)
        assert "5" in err.message
        assert err.error_code == AccountErrorCode.ACCOUNT_LIMIT_EXCEEDED

    def test_inherits_validation_error(self):
        err = AccountLimitExceededError(3, 3)
        assert isinstance(err, AccountValidationError)


class TestAccountReadOnlyExcessError:
    def test_fields(self):
        err = AccountReadOnlyExcessError(10, 6, 5)
        assert err.account_id == 10
        assert err.current_count == 6
        assert err.limit == 5
        assert "read-only" in err.message.lower()

    def test_error_code(self):
        err = AccountReadOnlyExcessError(1, 2, 1)
        assert err.error_code == "RECORD_READ_ONLY_EXCESS"
