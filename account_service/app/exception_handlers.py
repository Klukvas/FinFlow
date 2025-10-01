from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions import (
    AccountServiceError,
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    ExternalServiceError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "message": "Invalid request data"
        }
    )

def account_not_found_handler(request: Request, exc: AccountNotFoundError):
    """Handle account not found errors"""
    logger.warning(f"Account not found: {exc.account_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Account Not Found",
            "message": exc.message,
            "account_id": exc.account_id
        }
    )

def account_validation_handler(request: Request, exc: AccountValidationError):
    """Handle account validation errors"""
    logger.warning(f"Account validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Account Validation Error",
            "message": exc.message,
            "details": exc.details
        }
    )

def account_ownership_handler(request: Request, exc: AccountOwnershipError):
    """Handle account ownership errors"""
    logger.warning(f"Account ownership error: User {exc.user_id} doesn't own account {exc.account_id}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Account Ownership Error",
            "message": exc.message,
            "account_id": exc.account_id,
            "user_id": exc.user_id
        }
    )

def account_archived_handler(request: Request, exc: AccountArchivedError):
    """Handle archived account errors"""
    logger.warning(f"Archived account error: {exc.account_id}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Account Archived",
            "message": exc.message,
            "account_id": exc.account_id
        }
    )

def account_balance_handler(request: Request, exc: AccountBalanceError):
    """Handle account balance errors"""
    logger.warning(f"Account balance error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Account Balance Error",
            "message": exc.message,
            "details": exc.details
        }
    )

def external_service_handler(request: Request, exc: ExternalServiceError):
    """Handle external service errors"""
    logger.error(f"External service error: {exc.service} - {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "External Service Error",
            "message": f"Service {exc.service} is currently unavailable",
            "details": exc.details
        }
    )

def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )
