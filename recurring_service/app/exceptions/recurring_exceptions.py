class RecurringPaymentNotFoundError(Exception):
    """Исключение когда повторяющийся платеж не найден"""
    pass


class InvalidScheduleConfigError(Exception):
    """Исключение когда конфигурация расписания неверна"""
    pass


class PaymentExecutionError(Exception):
    """Исключение при выполнении платежа"""
    pass
