from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(str, Enum):
    # Expense related errors
    EXPENSE_NOT_FOUND = "EXPENSE_NOT_FOUND"
    EXPENSE_AMOUNT_INVALID = "EXPENSE_AMOUNT_INVALID"
    EXPENSE_AMOUNT_TOO_LARGE = "EXPENSE_AMOUNT_TOO_LARGE"
    EXPENSE_DATE_INVALID = "EXPENSE_DATE_INVALID"
    EXPENSE_DATE_FUTURE = "EXPENSE_DATE_FUTURE"
    EXPENSE_DATE_TOO_OLD = "EXPENSE_DATE_TOO_OLD"
    EXPENSE_DESCRIPTION_TOO_LONG = "EXPENSE_DESCRIPTION_TOO_LONG"
    EXPENSE_CREATION_FAILED = "EXPENSE_CREATION_FAILED"
    EXPENSE_UPDATE_FAILED = "EXPENSE_UPDATE_FAILED"
    EXPENSE_DELETE_FAILED = "EXPENSE_DELETE_FAILED"
    EXPENSE_RETRIEVAL_FAILED = "EXPENSE_RETRIEVAL_FAILED"
    
    # Category related errors
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    CATEGORY_NOT_OWNED = "CATEGORY_NOT_OWNED"
    CATEGORY_VALIDATION_FAILED = "CATEGORY_VALIDATION_FAILED"
    
    # Account related errors
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_NOT_OWNED = "ACCOUNT_NOT_OWNED"
    ACCOUNT_VALIDATION_FAILED = "ACCOUNT_VALIDATION_FAILED"
    ACCOUNT_BALANCE_UPDATE_FAILED = "ACCOUNT_BALANCE_UPDATE_FAILED"
    
    # External service errors
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    
    # Database errors
    DATABASE_CONSTRAINT_VIOLATION = "DATABASE_CONSTRAINT_VIOLATION"
    DATABASE_ERROR = "DATABASE_ERROR"

class StandardizedError(HTTPException):
    """Base class for standardized error responses with error and errorCode keys"""
    def __init__(self, status_code: int, error: str, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.details = details or {}
        
        # Create standardized response content
        content = {
            "error": error,
            "errorCode": error_code.value
        }
        
        # Add details if provided
        if self.details:
            content["details"] = self.details
            
        super().__init__(status_code=status_code, detail=content)

class CategoryValidationError(str, Enum):
    NOT_FOUND = "Category does not exist"
    SERVICE_ERROR = "Error validating category"
    NOT_OWNED = "Category does not belong to this user"
    WRONG_CATEGORY = "Category does not belong to the given category"

class ExpenseNotFoundError(StandardizedError):
    def __init__(self, expense_id: Optional[int] = None, detail: Optional[str] = None):
        if detail is None:
            detail = f"Expense with ID {expense_id} not found" if expense_id else "Expense not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error=detail,
            error_code=ErrorCode.EXPENSE_NOT_FOUND,
            details={"expense_id": expense_id} if expense_id else None
        )

class ExpenseValidationError(StandardizedError):
    def __init__(self, error: str, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=error,
            error_code=error_code,
            details=details
        )

class ExpenseAmountError(ExpenseValidationError):
    def __init__(self, amount: float, max_amount: float):
        super().__init__(
            error=f"Amount {amount} exceeds maximum allowed amount of {max_amount}",
            error_code=ErrorCode.EXPENSE_AMOUNT_TOO_LARGE,
            details={"amount": amount, "max_amount": max_amount}
        )

class ExpenseDateError(ExpenseValidationError):
    def __init__(self, date_str: str, error_type: str = "invalid_format"):
        if error_type == "future":
            super().__init__(
                error="Expense date cannot be in the future",
                error_code=ErrorCode.EXPENSE_DATE_FUTURE,
                details={"date": date_str}
            )
        elif error_type == "too_old":
            super().__init__(
                error="Expense date cannot be more than 10 years in the past",
                error_code=ErrorCode.EXPENSE_DATE_TOO_OLD,
                details={"date": date_str}
            )
        else:
            super().__init__(
                error=f"Invalid date format: {date_str}. Expected YYYY-MM-DD",
                error_code=ErrorCode.EXPENSE_DATE_INVALID,
                details={"date": date_str}
            )

class ExpenseDescriptionError(ExpenseValidationError):
    def __init__(self, length: int, max_length: int):
        super().__init__(
            error=f"Description length {length} exceeds maximum allowed length of {max_length} characters",
            error_code=ErrorCode.EXPENSE_DESCRIPTION_TOO_LONG,
            details={"length": length, "max_length": max_length}
        )

class ExternalServiceError(StandardizedError):
    def __init__(self, service: str, detail: str, error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error=f"External service {service} error: {detail}",
            error_code=error_code,
            details={"service": service, "original_error": detail}
        )