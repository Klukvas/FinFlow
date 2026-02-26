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
        super().__init__(message, "DEBT_VALIDATION_FAILED")

class ContactValidationError(DebtServiceException):
    """Raised when contact validation fails"""
    def __init__(self, message: str):
        super().__init__(message, "CONTACT_VALIDATION_FAILED")

class PaymentValidationError(DebtServiceException):
    """Raised when payment validation fails"""
    def __init__(self, message: str):
        super().__init__(message, "PAYMENT_VALIDATION_FAILED")

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

class ContactHasAssociatedDebtsError(DebtServiceException):
    """Raised when trying to delete a contact that has associated debts"""
    def __init__(self, contact_id: int, debt_count: int):
        super().__init__(f"Cannot delete contact with {debt_count} associated debts", "CONTACT_HAS_ASSOCIATED_DEBTS")
        self.contact_id = contact_id
        self.debt_count = debt_count

class DebtCreationFailedError(DebtServiceException):
    """Raised when debt creation fails"""
    def __init__(self, message: str = "Failed to create debt"):
        super().__init__(message, "DEBT_CREATION_FAILED")

class DebtUpdateFailedError(DebtServiceException):
    """Raised when debt update fails"""
    def __init__(self, message: str = "Failed to update debt"):
        super().__init__(message, "DEBT_UPDATE_FAILED")

class DebtDeletionFailedError(DebtServiceException):
    """Raised when debt deletion fails"""
    def __init__(self, message: str = "Failed to delete debt"):
        super().__init__(message, "DEBT_DELETION_FAILED")

class ContactCreationFailedError(DebtServiceException):
    """Raised when contact creation fails"""
    def __init__(self, message: str = "Failed to create contact"):
        super().__init__(message, "CONTACT_CREATION_FAILED")

class ContactUpdateFailedError(DebtServiceException):
    """Raised when contact update fails"""
    def __init__(self, message: str = "Failed to update contact"):
        super().__init__(message, "CONTACT_UPDATE_FAILED")

class ContactDeletionFailedError(DebtServiceException):
    """Raised when contact deletion fails"""
    def __init__(self, message: str = "Failed to delete contact"):
        super().__init__(message, "CONTACT_DELETION_FAILED")

class PaymentCreationFailedError(DebtServiceException):
    """Raised when payment creation fails"""
    def __init__(self, message: str = "Failed to create payment"):
        super().__init__(message, "PAYMENT_CREATION_FAILED")

class InvalidDebtTypeError(DebtServiceException):
    """Raised when an invalid debt type is provided"""
    def __init__(self, debt_type: str):
        super().__init__(f"Invalid debt type: {debt_type}", "INVALID_DEBT_TYPE")
        self.debt_type = debt_type

class InvalidPaymentMethodError(DebtServiceException):
    """Raised when an invalid payment method is provided"""
    def __init__(self, payment_method: str):
        super().__init__(f"Invalid payment method: {payment_method}", "INVALID_PAYMENT_METHOD")
        self.payment_method = payment_method

class DebtLimitExceededError(DebtValidationError):
    """Raised when user exceeds debt limit"""
    def __init__(self, current_count: int, limit: int):
        super().__init__(f"Debt limit exceeded. You have {current_count} debts but your plan allows only {limit} debts.")

class DebtReadOnlyExcessError(DebtServiceException):
    """Raised when debt exceeds plan limit and is read-only"""
    def __init__(self, debt_id: int, current_count: int, limit: int):
        super().__init__(
            f"This debt is read-only. You have {current_count} debts but your plan allows {limit}. Upgrade or delete excess debts.",
            "RECORD_READ_ONLY_EXCESS"
        )
        self.debt_id = debt_id
        self.current_count = current_count
        self.limit = limit
