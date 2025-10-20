# Error codes for unified error format
class IncomeErrorCodes:
    INCOME_NOT_FOUND = "INCOME_NOT_FOUND"
    INCOME_VALIDATION_FAILED = "INCOME_VALIDATION_FAILED"
    INCOME_AMOUNT_INVALID = "INCOME_AMOUNT_INVALID"
    INCOME_AMOUNT_TOO_LARGE = "INCOME_AMOUNT_TOO_LARGE"
    INCOME_AMOUNT_NEGATIVE = "INCOME_AMOUNT_NEGATIVE"
    INCOME_DATE_INVALID_FORMAT = "INCOME_DATE_INVALID_FORMAT"
    INCOME_DATE_FUTURE = "INCOME_DATE_FUTURE"
    INCOME_DESCRIPTION_TOO_LONG = "INCOME_DESCRIPTION_TOO_LONG"
    CATEGORY_VALIDATION_FAILED = "CATEGORY_VALIDATION_FAILED"
    ACCOUNT_VALIDATION_FAILED = "ACCOUNT_VALIDATION_FAILED"
    ACCOUNT_BALANCE_UPDATE_FAILED = "ACCOUNT_BALANCE_UPDATE_FAILED"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INCOME_LIMIT_EXCEEDED = "INCOME_LIMIT_EXCEEDED"


class IncomeError(Exception):
    """Base exception for income-related errors"""
    def __init__(self, message: str, error_code: str):
        self.error_code = error_code
        super().__init__(message)


class IncomeNotFoundError(IncomeError):
    """Raised when income is not found"""
    def __init__(self, message: str = "Income not found"):
        super().__init__(message, IncomeErrorCodes.INCOME_NOT_FOUND)


class IncomeValidationError(IncomeError):
    """Raised when income validation fails"""
    def __init__(self, message: str, error_code: str = IncomeErrorCodes.INCOME_VALIDATION_FAILED):
        super().__init__(message, error_code)


class IncomeAmountError(IncomeError):
    """Raised when income amount is invalid"""
    def __init__(self, message: str, error_code: str = IncomeErrorCodes.INCOME_AMOUNT_INVALID):
        super().__init__(message, error_code)


class IncomeDateError(IncomeError):
    """Raised when income date is invalid"""
    def __init__(self, message: str, error_code: str = IncomeErrorCodes.INCOME_DATE_INVALID_FORMAT):
        super().__init__(message, error_code)


class IncomeDescriptionError(IncomeError):
    """Raised when income description is invalid"""
    def __init__(self, message: str, error_code: str = IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG):
        super().__init__(message, error_code)


class ExternalServiceError(IncomeError):
    """Raised when external service call fails"""
    def __init__(self, message: str, service: str = None, error_code: str = IncomeErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE):
        self.service = service
        super().__init__(message, error_code)

class IncomeLimitExceededError(IncomeValidationError):
    """Raised when user exceeds income limit"""
    def __init__(self, current_count: int, limit: int):
        super().__init__(
            f"Income limit exceeded. You have {current_count} incomes but your plan allows only {limit} incomes.",
            IncomeErrorCodes.INCOME_LIMIT_EXCEEDED
        )
