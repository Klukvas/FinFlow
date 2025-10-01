from enum import Enum
from typing import Optional

class AccountServiceError(Exception):
    """Base exception for account service errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class AccountNotFoundError(AccountServiceError):
    """Raised when account is not found"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(f"Account with ID {account_id} not found")

class AccountValidationError(AccountServiceError):
    """Raised when account validation fails"""
    pass

class AccountOwnershipError(AccountServiceError):
    """Raised when user doesn't own the account"""
    def __init__(self, account_id: int, user_id: int):
        self.account_id = account_id
        self.user_id = user_id
        super().__init__(f"User {user_id} does not own account {account_id}")

class AccountArchivedError(AccountServiceError):
    """Raised when trying to perform operations on archived account"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(f"Account {account_id} is archived and cannot be modified")

class AccountBalanceError(AccountServiceError):
    """Raised when account balance operation fails"""
    pass

class ExternalServiceError(AccountServiceError):
    """Raised when external service call fails"""
    def __init__(self, service: str, detail: str):
        self.service = service
        super().__init__(f"External service error: {service}", detail)

class AccountValidationErrorCode(str, Enum):
    """Account validation error codes"""
    NOT_FOUND = "ACCOUNT_NOT_FOUND"
    NOT_OWNED = "ACCOUNT_NOT_OWNED"
    ARCHIVED = "ACCOUNT_ARCHIVED"
    INVALID_BALANCE = "INVALID_BALANCE"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    INVALID_TYPE = "INVALID_TYPE"
    SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
