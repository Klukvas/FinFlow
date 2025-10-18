from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryOwnershipError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with improved error messages"""
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "Validation error", "details": "Invalid request data"}
        )
    
    # Get the first error for backward compatibility
    first_error = errors[0]
    field = first_error["loc"][-1] if first_error["loc"] else "field"
    error_type = first_error["type"]
    error_msg = first_error.get("msg", "Invalid value")
    
    # Provide more specific error messages based on error type
    if error_type == "missing":
        message = f"{field.capitalize()} is required"
    elif error_type == "string_too_short":
        message = f"{field.capitalize()} must be at least 3 characters long"
    elif error_type == "greater_than":
        message = f"{field.capitalize()} must be greater than 0"
    else:
        message = f"{field.capitalize()}: {error_msg}"
    
    logger.warning(f"Validation error: {message} for field {field}")
    
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": message}
    )

async def category_exception_handler(request: Request, exc: HTTPException):
    """Handle all category-related exceptions with errorCode preservation"""
    # Log the error with the exception type name
    logger.warning(f"Category exception ({exc.__class__.__name__}): {exc.detail}")
    
    # Preserve the errorCode if it exists in the detail
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        content = {
            "error": exc.detail["error"],
            "errorCode": exc.detail["errorCode"]
        }
    else:
        content = {"error": exc.detail}
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    # Preserve the errorCode if it exists in the detail
    content = {"error": exc.detail}
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        content["errorCode"] = exc.detail["errorCode"]
        content["error"] = exc.detail["error"]
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )