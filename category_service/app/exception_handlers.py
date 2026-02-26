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
from app.config import settings
import json
import traceback

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with improved error messages"""
    errors = exc.errors()
    
    # Extract request context
    user_id = request.headers.get("X-User-Id", "unknown")
    workspace_id = request.headers.get("X-Workspace-Id", "unknown")
    
    # Try to get request body for logging
    try:
        body = await request.body()
        body_str = body.decode() if body else "empty"
    except Exception:
        body_str = "unable to read"
    
    if not errors:
        logger.error(
            "Pydantic validation error with no details",
            category="validation",
            operation="request_validation_error",
            method=request.method,
            path=str(request.url.path),
            user_id=user_id,
            workspace_id=workspace_id,
            request_body=body_str
        )
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
    
    # Detailed logging with all errors and request context
    logger.error(
        f"Pydantic validation error: {message}",
        category="validation",
        operation="request_validation_error",
        method=request.method,
        path=str(request.url.path),
        user_id=user_id,
        workspace_id=workspace_id,
        field=field,
        error_type=error_type,
        error_message=error_msg,
        all_errors=json.dumps(errors),
        request_body=body_str[:500]  # First 500 chars
    )
    
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": message}
    )

async def category_exception_handler(request: Request, exc: HTTPException):
    """Handle all category-related exceptions with errorCode preservation"""
    # Extract request context
    user_id = request.headers.get("X-User-Id", "unknown")
    workspace_id = request.headers.get("X-Workspace-Id", "unknown")
    auth_header = request.headers.get("Authorization", "")[:50]  # First 50 chars
    
    # Try to get request body for logging
    try:
        body = await request.body()
        body_str = body.decode() if body else "empty"
    except Exception:
        body_str = "unable to read"
    
    # Extract error details
    error_code = None
    error_message = exc.detail
    
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("errorCode")
        error_message = exc.detail.get("error", exc.detail)
    
    # Detailed logging with full context
    logger.error(
        f"Category exception: {exc.__class__.__name__} - {error_message}",
        category="business",
        operation="category_exception",
        exception_type=exc.__class__.__name__,
        method=request.method,
        path=str(request.url.path),
        status_code=exc.status_code,
        user_id=user_id,
        workspace_id=workspace_id,
        error_code=error_code,
        error_message=str(error_message),
        request_body=body_str[:500],  # First 500 chars
        auth_header_present=bool(auth_header),
        query_params=dict(request.query_params)
    )
    
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
    # Extract request context
    user_id = request.headers.get("X-User-Id", "unknown")
    workspace_id = request.headers.get("X-Workspace-Id", "unknown")
    
    # Try to get request body for logging
    try:
        body = await request.body()
        body_str = body.decode() if body else "empty"
    except Exception:
        body_str = "unable to read"
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        category="api",
        operation="http_exception",
        method=request.method,
        path=str(request.url.path),
        status_code=exc.status_code,
        user_id=user_id,
        workspace_id=workspace_id,
        error_detail=str(exc.detail),
        request_body=body_str[:500],
        query_params=dict(request.query_params)
    )
    
    # Preserve the errorCode if it exists in the detail
    content = {"error": exc.detail}
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        content["errorCode"] = exc.detail["errorCode"]
        content["error"] = exc.detail["error"]
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unexpected exceptions with full traceback"""
    # Extract request context
    user_id = request.headers.get("X-User-Id", "unknown")
    workspace_id = request.headers.get("X-Workspace-Id", "unknown")
    
    # Try to get request body for logging
    try:
        body = await request.body()
        body_str = body.decode() if body else "empty"
    except Exception:
        body_str = "unable to read"
    
    # Get full traceback
    tb_str = traceback.format_exc()
    
    # Log with all available context
    logger.error(
        f"Unexpected exception: {exc.__class__.__name__} - {str(exc)}",
        category="error",
        operation="unexpected_exception",
        exception_type=exc.__class__.__name__,
        exception_message=str(exc),
        method=request.method,
        path=str(request.url.path),
        user_id=user_id,
        workspace_id=workspace_id,
        request_body=body_str[:500],
        query_params=dict(request.query_params),
        headers={k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'x-internal-token']},
        traceback=tb_str
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "errorCode": "INTERNAL_SERVER_ERROR",
            "message": str(exc) if settings.LOG_LEVEL == "DEBUG" else "An unexpected error occurred"
        }
    )