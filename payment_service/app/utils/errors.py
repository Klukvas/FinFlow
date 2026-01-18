from __future__ import annotations

import logging
from typing import Optional, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("payment_service")


class ServiceError(Exception):
    """Base service error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthError(ServiceError):
    """Authentication/Authorization error"""

    def __init__(self, message: str, error_code: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class NotFoundError(ServiceError):
    """Resource not found error"""

    def __init__(self, message: str, error_code: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationError(ServiceError):
    """Validation error"""

    def __init__(self, message: str, error_code: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ConflictError(ServiceError):
    """Conflict error (e.g., duplicate resource)"""

    def __init__(self, message: str, error_code: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


async def service_exception_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Handle ServiceError exceptions"""
    logger.warning(
        f"Service error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "@payment_service/INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        },
    )
