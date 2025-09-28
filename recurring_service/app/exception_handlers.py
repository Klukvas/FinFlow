from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from app.exceptions import (
    RecurringPaymentNotFoundError,
    InvalidScheduleConfigError,
    PaymentExecutionError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def recurring_payment_not_found_handler(request: Request, exc: RecurringPaymentNotFoundError):
    """Обработчик для RecurringPaymentNotFoundError"""
    logger.warning(f"Recurring payment not found: {str(exc)}")
    return JSONResponse(
        status_code=404,
        content={"detail": "Recurring payment not found"}
    )


async def invalid_schedule_config_handler(request: Request, exc: InvalidScheduleConfigError):
    """Обработчик для InvalidScheduleConfigError"""
    logger.warning(f"Invalid schedule config: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid schedule configuration: {str(exc)}"}
    )


async def payment_execution_error_handler(request: Request, exc: PaymentExecutionError):
    """Обработчик для PaymentExecutionError"""
    logger.error(f"Payment execution error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Payment execution failed: {str(exc)}"}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик для HTTPException"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик для общих исключений"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
