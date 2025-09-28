class IncomeError(Exception):
    """Base exception for income-related errors"""
    pass

class IncomeNotFoundError(IncomeError):
    """Raised when income is not found"""
    pass

class IncomeValidationError(IncomeError):
    """Raised when income validation fails"""
    pass

class IncomeAmountError(IncomeError):
    """Raised when income amount is invalid"""
    pass

class IncomeDateError(IncomeError):
    """Raised when income date is invalid"""
    pass

class IncomeDescriptionError(IncomeError):
    """Raised when income description is invalid"""
    pass

class ExternalServiceError(IncomeError):
    """Raised when external service call fails"""
    def __init__(self, service: str = None, detail: str = None):
        self.service = service
        self.detail = detail
        super().__init__(f"External service error: {service} - {detail}")
