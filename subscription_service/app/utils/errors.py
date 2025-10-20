from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging


logger = logging.getLogger("subscription_service.errors")


class ServiceError(Exception):
    error_code: str = "@subscription_service/INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, error_code: Optional[str] = None, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.message = message


class NotFoundError(ServiceError):
    status_code = 404


class ValidationError(ServiceError):
    status_code = 400


class ConflictError(ServiceError):
    status_code = 409


class AuthError(ServiceError):
    status_code = 401


def error_response(message: str, error_code: str, status_code: int) -> JSONResponse:
    return JSONResponse(content={"error": message, "errorCode": error_code}, status_code=status_code)


async def service_exception_handler(request: Request, exc: ServiceError):
    logger.warning("service_error", extra={"error_code": exc.error_code, "path": request.url.path})
    return error_response(exc.message, exc.error_code, exc.status_code)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", extra={"path": request.url.path})
    return error_response("Internal server error", "@subscription_service/INTERNAL_ERROR", 500)


