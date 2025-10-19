"""
Exception handlers for currency service.
Converts custom exceptions to HTTP responses with unified error format.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.exceptions import (
    CurrencyError,
    UnsupportedCurrencyError,
    CurrencyServiceUnavailableError,
    CurrencyConversionFailedError,
    CurrencyRatesFetchFailedError,
    CurrencyCacheError,
    CurrencyValidationError,
    ExternalApiError,
    RedisConnectionError
)


async def currency_error_handler(request: Request, exc: CurrencyError) -> JSONResponse:
    """Handle currency service errors with unified format"""
    
    # Map currency errors to appropriate HTTP status codes
    status_code_map = {
        UnsupportedCurrencyError: status.HTTP_400_BAD_REQUEST,
        CurrencyValidationError: status.HTTP_400_BAD_REQUEST,
        CurrencyServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
        CurrencyConversionFailedError: status.HTTP_503_SERVICE_UNAVAILABLE,
        CurrencyRatesFetchFailedError: status.HTTP_503_SERVICE_UNAVAILABLE,
        CurrencyCacheError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ExternalApiError: status.HTTP_503_SERVICE_UNAVAILABLE,
        RedisConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    http_status = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=http_status,
        content=exc.to_dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions with unified format"""
    
    # Extract error details from HTTPException
    error_detail = exc.detail
    if isinstance(error_detail, dict):
        # If detail is already a dict, use it directly
        error_content = error_detail
    else:
        # Convert string detail to unified format
        error_content = {
            "error": str(error_detail),
            "errorCode": "HTTP_ERROR"
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_content
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with unified format"""
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error occurred",
            "errorCode": "INTERNAL_SERVER_ERROR",
            "details": {
                "type": type(exc).__name__,
                "message": str(exc)
            }
        }
    )
