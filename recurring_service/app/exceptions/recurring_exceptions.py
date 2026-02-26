class BaseRecurringError(Exception):
    """Базовое исключение для сервиса повторяющихся платежей"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class RecurringPaymentNotFoundError(BaseRecurringError):
    """Исключение когда повторяющийся платеж не найден"""
    def __init__(self, message: str = "Recurring payment not found"):
        super().__init__(message, "RECURRING_PAYMENT_NOT_FOUND")


class InvalidScheduleConfigError(BaseRecurringError):
    """Исключение когда конфигурация расписания неверна"""
    def __init__(self, message: str = "Invalid schedule configuration"):
        super().__init__(message, "INVALID_SCHEDULE_CONFIG")


class PaymentExecutionError(BaseRecurringError):
    """Исключение при выполнении платежа"""
    def __init__(self, message: str = "Payment execution failed"):
        super().__init__(message, "PAYMENT_EXECUTION_FAILED")


class CategoryNotFoundError(BaseRecurringError):
    """Исключение когда категория не найдена"""
    def __init__(self, message: str = "Category not found"):
        super().__init__(message, "CATEGORY_NOT_FOUND")


class InvalidPaymentStatusError(BaseRecurringError):
    """Исключение при неверном статусе платежа"""
    def __init__(self, message: str = "Invalid payment status"):
        super().__init__(message, "INVALID_PAYMENT_STATUS")


class PaymentAlreadyPausedError(BaseRecurringError):
    """Исключение когда платеж уже приостановлен"""
    def __init__(self, message: str = "Payment is already paused"):
        super().__init__(message, "PAYMENT_ALREADY_PAUSED")


class PaymentNotPausedError(BaseRecurringError):
    """Исключение когда платеж не приостановлен"""
    def __init__(self, message: str = "Payment is not paused"):
        super().__init__(message, "PAYMENT_NOT_PAUSED")


class ScheduleNotFoundError(BaseRecurringError):
    """Исключение когда расписание не найдено"""
    def __init__(self, message: str = "Payment schedule not found"):
        super().__init__(message, "SCHEDULE_NOT_FOUND")


class InvalidScheduleStatusError(BaseRecurringError):
    """Исключение при неверном статусе расписания"""
    def __init__(self, message: str = "Invalid schedule status"):
        super().__init__(message, "INVALID_SCHEDULE_STATUS")


class ServiceClientError(BaseRecurringError):
    """Исключение при ошибке клиента внешнего сервиса"""
    def __init__(self, message: str = "External service client error"):
        super().__init__(message, "SERVICE_CLIENT_ERROR")


class DatabaseError(BaseRecurringError):
    """Исключение при ошибке базы данных"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")


class ValidationError(BaseRecurringError):
    """Исключение при ошибке валидации"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class InternalServerError(BaseRecurringError):
    """Исключение при внутренней ошибке сервера"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, "INTERNAL_SERVER_ERROR")

class RecurringLimitExceededError(BaseRecurringError):
    """Исключение когда превышен лимит повторяющихся платежей"""
    def __init__(self, current_count: int, limit: int):
        super().__init__(
            f"Recurring payment limit exceeded. You have {current_count} recurring payments but your plan allows only {limit} recurring payments.",
            "RECURRING_LIMIT_EXCEEDED"
        )


class RecurringReadOnlyExcessError(BaseRecurringError):
    """Raised when recurring payment exceeds plan limit and is read-only"""
    def __init__(self, payment_id, current_count: int, limit: int):
        super().__init__(
            f"This recurring payment is read-only. You have {current_count} recurring payments but your plan allows {limit}. Upgrade or delete excess recurring payments.",
            "RECORD_READ_ONLY_EXCESS"
        )
        self.payment_id = payment_id
        self.current_count = current_count
        self.limit = limit
