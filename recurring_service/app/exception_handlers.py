from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from app.exceptions import (
    BaseRecurringError,
    RecurringPaymentNotFoundError,
    InvalidScheduleConfigError,
    PaymentExecutionError,
    CategoryNotFoundError,
    InvalidPaymentStatusError,
    PaymentAlreadyPausedError,
    PaymentNotPausedError,
    ScheduleNotFoundError,
    InvalidScheduleStatusError,
    ServiceClientError,
    DatabaseError,
    ValidationError,
    InternalServerError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def base_recurring_error_handler(request: Request, exc: BaseRecurringError):
    """Универсальный обработчик для всех BaseRecurringError"""
    logger.warning(f"Recurring service error: {exc.error_code} - {exc.message}")
    
    # Определяем статус код на основе типа ошибки
    status_code = 500  # по умолчанию
    
    if isinstance(exc, (RecurringPaymentNotFoundError, ScheduleNotFoundError)):
        status_code = 404
    elif isinstance(exc, (
        InvalidScheduleConfigError, 
        CategoryNotFoundError,
        InvalidPaymentStatusError,
        PaymentAlreadyPausedError,
        PaymentNotPausedError,
        InvalidScheduleStatusError,
        ValidationError
    )):
        status_code = 400
    elif isinstance(exc, (PaymentExecutionError, ServiceClientError, DatabaseError)):
        status_code = 500
    elif isinstance(exc, InternalServerError):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def recurring_payment_not_found_handler(request: Request, exc: RecurringPaymentNotFoundError):
    """Обработчик для RecurringPaymentNotFoundError"""
    logger.warning(f"Recurring payment not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def invalid_schedule_config_handler(request: Request, exc: InvalidScheduleConfigError):
    """Обработчик для InvalidScheduleConfigError"""
    logger.warning(f"Invalid schedule config: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def payment_execution_error_handler(request: Request, exc: PaymentExecutionError):
    """Обработчик для PaymentExecutionError"""
    logger.error(f"Payment execution error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def category_not_found_handler(request: Request, exc: CategoryNotFoundError):
    """Обработчик для CategoryNotFoundError"""
    logger.warning(f"Category not found: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def validation_error_handler(request: Request, exc: ValidationError):
    """Обработчик для ValidationError"""
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик для HTTPException"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "errorCode": "HTTP_EXCEPTION"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик для общих исключений"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "errorCode": "INTERNAL_SERVER_ERROR"
        }
    )
