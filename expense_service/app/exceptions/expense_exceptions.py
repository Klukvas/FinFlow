from fastapi import HTTPException, status
from typing import Optional
from enum import Enum

class CategoryValidationError(str, Enum):
    NOT_FOUND = "Category does not exist"
    SERVICE_ERROR = "Error validating category"
    NOT_OWNED = "Category does not belong to this user"
    WRONG_CATEGORY = "Category does not belong to the given category"

class ExpenseNotFoundError(HTTPException):
    def __init__(self, expense_id: Optional[int] = None, detail: Optional[str] = None):
        if detail is None:
            detail = f"Expense with ID {expense_id} not found" if expense_id else "Expense not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class ExpenseValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class ExpenseAmountError(ExpenseValidationError):
    def __init__(self, amount: float, max_amount: float):
        super().__init__(
            detail=f"Amount {amount} exceeds maximum allowed amount of {max_amount}"
        )

class ExpenseDateError(ExpenseValidationError):
    def __init__(self, date_str: str):
        super().__init__(
            detail=f"Invalid date format: {date_str}. Expected YYYY-MM-DD"
        )

class ExpenseDescriptionError(ExpenseValidationError):
    def __init__(self, length: int, max_length: int):
        super().__init__(
            detail=f"Description length {length} exceeds maximum allowed length of {max_length} characters"
        )

class ExternalServiceError(HTTPException):
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External service {service} error: {detail}"
        )