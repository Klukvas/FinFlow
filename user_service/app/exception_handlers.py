from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from app.exceptions.user_errors import (
    UserNotFoundError,
    UserValidationError,
    UserAuthenticationError,
    UserRegistrationError,
    PasswordPolicyError,
    UsernamePolicyError,
    AccountLockedError,
    RateLimitError,
    UserErrorCode
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with improved error messages"""
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "Validation error", "errorCode": UserErrorCode.VALIDATION_ERROR}
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
        message = f"{field.capitalize()} must be at least {first_error.get('ctx', {}).get('min_length', '')} characters long"
    elif error_type == "string_too_long":
        message = f"{field.capitalize()} must be no more than {first_error.get('ctx', {}).get('max_length', '')} characters long"
    elif error_type == "value_error":
        message = error_msg
    else:
        message = f"{field.capitalize()}: {error_msg}"
    
    logger.warning(f"Validation error: {message} for field {field}")
    
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": message, "errorCode": UserErrorCode.VALIDATION_ERROR}
    )

async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """Handle user not found errors"""
    logger.info(f"User not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def user_validation_handler(request: Request, exc: UserValidationError):
    """Handle user validation errors"""
    logger.warning(f"User validation error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def user_authentication_handler(request: Request, exc: UserAuthenticationError):
    """Handle user authentication errors"""
    logger.warning(f"User authentication error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def user_registration_handler(request: Request, exc: UserRegistrationError):
    """Handle user registration errors"""
    logger.warning(f"User registration error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def password_policy_handler(request: Request, exc: PasswordPolicyError):
    """Handle password policy errors"""
    logger.warning(f"Password policy error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def username_policy_handler(request: Request, exc: UsernamePolicyError):
    """Handle username policy errors"""
    logger.warning(f"Username policy error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def account_locked_handler(request: Request, exc: AccountLockedError):
    """Handle account locked errors"""
    logger.warning(f"Account locked: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def rate_limit_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit exceeded: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": UserErrorCode.INTERNAL_ERROR}
    )