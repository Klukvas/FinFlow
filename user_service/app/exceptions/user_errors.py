from fastapi import HTTPException, status
from typing import Optional
from enum import Enum

class UserServiceError(str, Enum):
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    USERNAME_ALREADY_REGISTERED = "Username already registered"
    INVALID_CREDENTIALS = "Invalid email or password"
    USER_NOT_FOUND = "User not found"
    UNAUTHORIZED = "Unauthorized"
    INVALID_TOKEN = "Invalid token"
    ACCOUNT_LOCKED = "Account is temporarily locked due to too many failed login attempts"
    WEAK_PASSWORD = "Password does not meet security requirements"
    INVALID_USERNAME = "Username does not meet requirements"
    INVALID_EMAIL = "Invalid email format"
    RATE_LIMIT_EXCEEDED = "Too many requests, please try again later"

class UserErrorCode(str, Enum):
    EMAIL_ALREADY_TAKEN = "EMAIL_ALREADY_TAKEN"
    USERNAME_ALREADY_TAKEN = "USERNAME_ALREADY_TAKEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_USERNAME = "INVALID_USERNAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    REGISTRATION_ERROR = "REGISTRATION_ERROR"
    PASSWORD_POLICY_ERROR = "PASSWORD_POLICY_ERROR"
    USERNAME_POLICY_ERROR = "USERNAME_POLICY_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class UserNotFoundError(HTTPException):
    def __init__(self, user_id: Optional[int] = None, detail: Optional[str] = None):
        if detail is None:
            detail = f"User with ID {user_id} not found" if user_id else "User not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        self.error_code = UserErrorCode.USER_NOT_FOUND

class UserValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.error_code = UserErrorCode.VALIDATION_ERROR

class UserAuthenticationError(HTTPException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
        self.error_code = UserErrorCode.INVALID_CREDENTIALS

class UserRegistrationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.error_code = UserErrorCode.REGISTRATION_ERROR

class PasswordPolicyError(UserValidationError):
    def __init__(self, detail: str):
        super().__init__(detail=f"Password policy violation: {detail}")
        self.error_code = UserErrorCode.PASSWORD_POLICY_ERROR

class UsernamePolicyError(UserValidationError):
    def __init__(self, detail: str):
        super().__init__(detail=f"Username policy violation: {detail}")
        self.error_code = UserErrorCode.USERNAME_POLICY_ERROR

class AccountLockedError(HTTPException):
    def __init__(self, lockout_duration: int):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is temporarily locked due to too many failed login attempts. Try again in {lockout_duration} minutes."
        )
        self.error_code = UserErrorCode.ACCOUNT_LOCKED

class RateLimitError(HTTPException):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds."
        )
        self.error_code = UserErrorCode.RATE_LIMIT_EXCEEDED