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

async def category_not_found_handler(request: Request, exc: CategoryNotFoundError):
    """Handle category not found errors"""
    logger.info(f"Category not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def category_validation_handler(request: Request, exc: CategoryValidationError):
    """Handle category validation errors"""
    logger.warning(f"Category validation error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def category_ownership_handler(request: Request, exc: CategoryOwnershipError):
    """Handle category ownership errors"""
    logger.warning(f"Category ownership error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def circular_relationship_handler(request: Request, exc: CircularRelationshipError):
    """Handle circular relationship errors"""
    logger.warning(f"Circular relationship error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def category_depth_handler(request: Request, exc: CategoryDepthExceededError):
    """Handle category depth exceeded errors"""
    logger.warning(f"Category depth exceeded: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def category_name_conflict_handler(request: Request, exc: CategoryNameConflictError):
    """Handle category name conflict errors"""
    logger.warning(f"Category name conflict: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )