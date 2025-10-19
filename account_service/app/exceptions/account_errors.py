from enum import Enum
from typing import Optional
class AccountErrorCode(str, Enum):
    """Account service error codes"""
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_NOT_OWNED = "ACCOUNT_NOT_OWNED"
    ACCOUNT_ARCHIVED = "ACCOUNT_ARCHIVED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_BALANCE = "INVALID_BALANCE"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    INVALID_ACCOUNT_NAME = "INVALID_ACCOUNT_NAME"
    INVALID_ACCOUNT_DESCRIPTION = "INVALID_ACCOUNT_DESCRIPTION"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CURRENCY_CONVERSION_FAILED = "CURRENCY_CONVERSION_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class AccountServiceError(Exception):
    """Base exception for account service errors"""
    def __init__(self, message: str, error_code: str, details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class AccountNotFoundError(AccountServiceError):
    """Raised when account is not found"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(
            f"Account with ID {account_id} not found",
            AccountErrorCode.ACCOUNT_NOT_FOUND
        )

class AccountValidationError(AccountServiceError):
    """Raised when account validation fails"""
    def __init__(self, message: str, error_code: str = AccountErrorCode.VALIDATION_ERROR, details: Optional[str] = None):
        super().__init__(message, error_code, details)

class AccountOwnershipError(AccountServiceError):
    """Raised when user doesn't own the account"""
    def __init__(self, account_id: int, user_id: int):
        self.account_id = account_id
        self.user_id = user_id
        super().__init__(
            f"User {user_id} does not own account {account_id}",
            AccountErrorCode.ACCOUNT_NOT_OWNED
        )

class AccountArchivedError(AccountServiceError):
    """Raised when trying to perform operations on archived account"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(
            f"Account {account_id} is archived and cannot be modified",
            AccountErrorCode.ACCOUNT_ARCHIVED
        )

class AccountBalanceError(AccountServiceError):
    """Raised when account balance operation fails"""
    def __init__(self, message: str, error_code: str = AccountErrorCode.INVALID_BALANCE, details: Optional[str] = None):
        super().__init__(message, error_code, details)

class ExternalServiceError(AccountServiceError):
    """Raised when external service call fails"""
    def __init__(self, service: str, detail: str):
        self.service = service
        super().__init__(
            f"External service error: {service}",
            AccountErrorCode.EXTERNAL_SERVICE_ERROR,
            detail
        )
