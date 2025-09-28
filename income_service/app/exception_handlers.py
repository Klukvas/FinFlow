from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": errors}
    )

async def income_not_found_handler(request: Request, exc: IncomeNotFoundError):
    """Handle income not found errors"""
    logger.warning(f"Income not found: {str(exc)}")
    return JSONResponse(
        status_code=404,
        content={"error": "Income not found"}
    )

async def income_validation_handler(request: Request, exc: IncomeValidationError):
    """Handle income validation errors"""
    logger.warning(f"Income validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": "Income validation error", "details": str(exc)}
    )

async def income_amount_handler(request: Request, exc: IncomeAmountError):
    """Handle income amount errors"""
    logger.warning(f"Income amount error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid income amount", "details": str(exc)}
    )

async def income_date_handler(request: Request, exc: IncomeDateError):
    """Handle income date errors"""
    logger.warning(f"Income date error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid income date", "details": str(exc)}
    )

async def income_description_handler(request: Request, exc: IncomeDescriptionError):
    """Handle income description errors"""
    logger.warning(f"Income description error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid income description", "details": str(exc)}
    )

async def external_service_handler(request: Request, exc: ExternalServiceError):
    """Handle external service errors"""
    logger.error(f"External service error: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={"error": "External service unavailable", "details": str(exc)}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
