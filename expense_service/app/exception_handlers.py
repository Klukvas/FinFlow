from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from app.exceptions import (
    ErrorCode,
    StandardizedError,
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized error format"""
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation error",
                "errorCode": ErrorCode.VALIDATION_ERROR.value,
                "details": {"message": "Invalid request data"}
            }
        )
    
    # Get the first error for backward compatibility
    first_error = errors[0]
    field = first_error["loc"][-1] if first_error["loc"] else "field"
    error_type = first_error["type"]
    error_msg = first_error.get("msg", "Invalid value")
    
    # Determine error code based on error type
    if error_type == "missing":
        error_code = ErrorCode.MISSING_REQUIRED_FIELD
        message = f"{field.capitalize()} is required"
    elif error_type == "greater_than":
        error_code = ErrorCode.INVALID_FIELD_VALUE
        message = f"{field.capitalize()} must be greater than 0"
    elif error_type == "less_than_equal":
        error_code = ErrorCode.INVALID_FIELD_VALUE
        message = f"{field.capitalize()} exceeds maximum allowed value"
    elif error_type == "string_too_long":
        error_code = ErrorCode.INVALID_FIELD_VALUE
        message = f"{field.capitalize()} exceeds maximum length"
    else:
        error_code = ErrorCode.INVALID_FIELD_VALUE
        message = f"{field.capitalize()}: {error_msg}"
    
    logger.warning(f"Validation error: {message} for field {field}")
    
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "error": message,
            "errorCode": error_code.value,
            "details": {"field": field, "error_type": error_type}
        }
    )

async def standardized_error_handler(request: Request, exc: StandardizedError):
    """Handle all standardized errors with consistent format"""
    logger.warning(f"Standardized error: {exc.error_code.value} - {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def expense_not_found_handler(request: Request, exc: ExpenseNotFoundError):
    """Handle expense not found errors"""
    logger.info(f"Expense not found: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def expense_validation_handler(request: Request, exc: ExpenseValidationError):
    """Handle expense validation errors"""
    logger.warning(f"Expense validation error: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def expense_amount_handler(request: Request, exc: ExpenseAmountError):
    """Handle expense amount errors"""
    logger.warning(f"Expense amount error: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def expense_date_handler(request: Request, exc: ExpenseDateError):
    """Handle expense date errors"""
    logger.warning(f"Expense date error: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def expense_description_handler(request: Request, exc: ExpenseDescriptionError):
    """Handle expense description errors"""
    logger.warning(f"Expense description error: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def external_service_handler(request: Request, exc: ExternalServiceError):
    """Handle external service errors"""
    logger.error(f"External service error: {exc.detail['error']}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions with standardized format"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    # Check if it's already a standardized error
    if isinstance(exc.detail, dict) and "error" in exc.detail and "errorCode" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Convert to standardized format
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "errorCode": ErrorCode.VALIDATION_ERROR.value
        }
    )
