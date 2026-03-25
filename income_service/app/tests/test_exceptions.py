"""Tests for app/exceptions/income_errors.py — all exception classes and error codes."""
import pytest

from app.exceptions import (
    IncomeError,
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError,
    IncomeLimitExceededError,
    IncomeErrorCodes,
)


# ---------------------------------------------------------------------------
# IncomeErrorCodes
# ---------------------------------------------------------------------------
class TestIncomeErrorCodes:
    def test_income_not_found_code(self):
        assert IncomeErrorCodes.INCOME_NOT_FOUND == "INCOME_NOT_FOUND"

    def test_validation_failed_code(self):
        assert IncomeErrorCodes.INCOME_VALIDATION_FAILED == "INCOME_VALIDATION_FAILED"

    def test_amount_invalid_code(self):
        assert IncomeErrorCodes.INCOME_AMOUNT_INVALID == "INCOME_AMOUNT_INVALID"

    def test_amount_too_large_code(self):
        assert IncomeErrorCodes.INCOME_AMOUNT_TOO_LARGE == "INCOME_AMOUNT_TOO_LARGE"

    def test_amount_negative_code(self):
        assert IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE == "INCOME_AMOUNT_NEGATIVE"

    def test_date_invalid_format_code(self):
        assert IncomeErrorCodes.INCOME_DATE_INVALID_FORMAT == "INCOME_DATE_INVALID_FORMAT"

    def test_date_future_code(self):
        assert IncomeErrorCodes.INCOME_DATE_FUTURE == "INCOME_DATE_FUTURE"

    def test_description_too_long_code(self):
        assert IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG == "INCOME_DESCRIPTION_TOO_LONG"

    def test_category_validation_failed_code(self):
        assert IncomeErrorCodes.CATEGORY_VALIDATION_FAILED == "CATEGORY_VALIDATION_FAILED"

    def test_account_validation_failed_code(self):
        assert IncomeErrorCodes.ACCOUNT_VALIDATION_FAILED == "ACCOUNT_VALIDATION_FAILED"

    def test_account_balance_update_failed_code(self):
        assert IncomeErrorCodes.ACCOUNT_BALANCE_UPDATE_FAILED == "ACCOUNT_BALANCE_UPDATE_FAILED"

    def test_external_service_unavailable_code(self):
        assert IncomeErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE == "EXTERNAL_SERVICE_UNAVAILABLE"

    def test_validation_error_code(self):
        assert IncomeErrorCodes.VALIDATION_ERROR == "VALIDATION_ERROR"

    def test_income_limit_exceeded_code(self):
        assert IncomeErrorCodes.INCOME_LIMIT_EXCEEDED == "INCOME_LIMIT_EXCEEDED"


# ---------------------------------------------------------------------------
# IncomeError (base)
# ---------------------------------------------------------------------------
class TestIncomeError:
    def test_message_and_error_code(self):
        err = IncomeError("something went wrong", "CUSTOM_CODE")
        assert str(err) == "something went wrong"
        assert err.error_code == "CUSTOM_CODE"

    def test_is_exception(self):
        err = IncomeError("test", "CODE")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# IncomeNotFoundError
# ---------------------------------------------------------------------------
class TestIncomeNotFoundError:
    def test_default_message(self):
        err = IncomeNotFoundError()
        assert str(err) == "Income not found"
        assert err.error_code == IncomeErrorCodes.INCOME_NOT_FOUND

    def test_custom_message(self):
        err = IncomeNotFoundError("Income 42 not found")
        assert "42" in str(err)
        assert err.error_code == IncomeErrorCodes.INCOME_NOT_FOUND

    def test_inherits_income_error(self):
        assert issubclass(IncomeNotFoundError, IncomeError)


# ---------------------------------------------------------------------------
# IncomeValidationError
# ---------------------------------------------------------------------------
class TestIncomeValidationError:
    def test_default_error_code(self):
        err = IncomeValidationError("bad data")
        assert err.error_code == IncomeErrorCodes.INCOME_VALIDATION_FAILED

    def test_custom_error_code(self):
        err = IncomeValidationError("bad data", "CUSTOM")
        assert err.error_code == "CUSTOM"

    def test_inherits_income_error(self):
        assert issubclass(IncomeValidationError, IncomeError)


# ---------------------------------------------------------------------------
# IncomeAmountError
# ---------------------------------------------------------------------------
class TestIncomeAmountError:
    def test_default_error_code(self):
        err = IncomeAmountError("too much")
        assert err.error_code == IncomeErrorCodes.INCOME_AMOUNT_INVALID

    def test_custom_error_code(self):
        err = IncomeAmountError("negative", IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE)
        assert err.error_code == IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE

    def test_inherits_income_error(self):
        assert issubclass(IncomeAmountError, IncomeError)


# ---------------------------------------------------------------------------
# IncomeDateError
# ---------------------------------------------------------------------------
class TestIncomeDateError:
    def test_default_error_code(self):
        err = IncomeDateError("wrong format")
        assert err.error_code == IncomeErrorCodes.INCOME_DATE_INVALID_FORMAT

    def test_custom_error_code(self):
        err = IncomeDateError("future", IncomeErrorCodes.INCOME_DATE_FUTURE)
        assert err.error_code == IncomeErrorCodes.INCOME_DATE_FUTURE

    def test_inherits_income_error(self):
        assert issubclass(IncomeDateError, IncomeError)


# ---------------------------------------------------------------------------
# IncomeDescriptionError
# ---------------------------------------------------------------------------
class TestIncomeDescriptionError:
    def test_default_error_code(self):
        err = IncomeDescriptionError("too long")
        assert err.error_code == IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG

    def test_inherits_income_error(self):
        assert issubclass(IncomeDescriptionError, IncomeError)


# ---------------------------------------------------------------------------
# ExternalServiceError
# ---------------------------------------------------------------------------
class TestExternalServiceError:
    def test_default_error_code(self):
        err = ExternalServiceError("timeout")
        assert err.error_code == IncomeErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE

    def test_service_attribute(self):
        err = ExternalServiceError("down", service="account-service")
        assert err.service == "account-service"

    def test_service_none_by_default(self):
        err = ExternalServiceError("err")
        assert err.service is None

    def test_custom_error_code(self):
        err = ExternalServiceError("err", error_code="CUSTOM")
        assert err.error_code == "CUSTOM"

    def test_inherits_income_error(self):
        assert issubclass(ExternalServiceError, IncomeError)


# ---------------------------------------------------------------------------
# IncomeLimitExceededError
# ---------------------------------------------------------------------------
class TestIncomeLimitExceededError:
    def test_message_includes_counts(self):
        err = IncomeLimitExceededError(current_count=50, limit=50)
        assert "50" in str(err)
        assert err.error_code == IncomeErrorCodes.INCOME_LIMIT_EXCEEDED

    def test_inherits_income_validation_error(self):
        assert issubclass(IncomeLimitExceededError, IncomeValidationError)

    def test_zero_limit(self):
        err = IncomeLimitExceededError(current_count=0, limit=0)
        assert "0" in str(err)
