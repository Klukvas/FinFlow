from fastapi import HTTPException
from typing import Any, Dict, Optional

class DebtServiceException(Exception):
    """Base exception for debt service"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DebtNotFoundError(DebtServiceException):
    """Raised when a debt is not found"""
    def __init__(self, debt_id: int):
        super().__init__(f"Debt with ID {debt_id} not found", "DEBT_NOT_FOUND")
        self.debt_id = debt_id

class ContactNotFoundError(DebtServiceException):
    """Raised when a contact is not found"""
    def __init__(self, contact_id: int):
        super().__init__(f"Contact with ID {contact_id} not found", "CONTACT_NOT_FOUND")
        self.contact_id = contact_id

class PaymentNotFoundError(DebtServiceException):
    """Raised when a payment is not found"""
    def __init__(self, payment_id: int):
        super().__init__(f"Payment with ID {payment_id} not found", "PAYMENT_NOT_FOUND")
        self.payment_id = payment_id

class DebtValidationError(DebtServiceException):
    """Raised when debt validation fails"""
    def __init__(self, message: str):
        super().__init__(message, "DEBT_VALIDATION_ERROR")

class ContactValidationError(DebtServiceException):
    """Raised when contact validation fails"""
    def __init__(self, message: str):
        super().__init__(message, "CONTACT_VALIDATION_ERROR")

class PaymentValidationError(DebtServiceException):
    """Raised when payment validation fails"""
    def __init__(self, message: str):
        super().__init__(message, "PAYMENT_VALIDATION_ERROR")

class DebtAmountError(DebtServiceException):
    """Raised when debt amount is invalid"""
    def __init__(self, amount: float, max_amount: float = 999999.99):
        super().__init__(f"Debt amount {amount} must be between 0 and {max_amount}", "INVALID_DEBT_AMOUNT")
        self.amount = amount
        self.max_amount = max_amount

class PaymentAmountError(DebtServiceException):
    """Raised when payment amount is invalid"""
    def __init__(self, amount: float, remaining_balance: float):
        super().__init__(f"Payment amount {amount} exceeds remaining balance {remaining_balance}", "PAYMENT_AMOUNT_EXCEEDS_BALANCE")
        self.amount = amount
        self.remaining_balance = remaining_balance

class DebtDateError(DebtServiceException):
    """Raised when debt date is invalid"""
    def __init__(self, message: str):
        super().__init__(f"Invalid date: {message}", "INVALID_DEBT_DATE")

class ExternalServiceError(DebtServiceException):
    """Raised when external service communication fails"""
    def __init__(self, service_name: str, message: str):
        super().__init__(f"External service error ({service_name}): {message}", "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name

class DatabaseError(DebtServiceException):
    """Raised when database operation fails"""
    def __init__(self, message: str, operation: str):
        super().__init__(f"Database error during {operation}: {message}", "DATABASE_ERROR")
        self.operation = operation
