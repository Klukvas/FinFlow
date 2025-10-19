"""
Currency service error definitions with unified format.
All errors follow the format: {"error": <string>, "errorCode": <STRING_CONSTANT>}
"""

from typing import Dict, Any


class CurrencyError(Exception):
    """Base exception for currency service errors"""
    
    def __init__(self, error: str, error_code: str, details: Dict[str, Any] = None):
        self.error = error
        self.error_code = error_code
        self.details = details or {}
        super().__init__(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to unified format dictionary"""
        result = {
            "error": self.error,
            "errorCode": self.error_code
        }
        if self.details:
            result.update(self.details)
        return result


class UnsupportedCurrencyError(CurrencyError):
    """Raised when a currency code is not supported"""
    
    def __init__(self, currency_code: str, is_source: bool = True):
        error_type = "source" if is_source else "target"
        super().__init__(
            error=f"Unsupported {error_type} currency: {currency_code}",
            error_code="UNSUPPORTED_CURRENCY",
            details={
                "currency": currency_code,
                "type": error_type
            }
        )


class CurrencyServiceUnavailableError(CurrencyError):
    """Raised when currency service is temporarily unavailable"""
    
    def __init__(self, operation: str = "currency operation"):
        super().__init__(
            error=f"Currency service is temporarily unavailable for {operation}",
            error_code="CURRENCY_SERVICE_UNAVAILABLE",
            details={
                "operation": operation
            }
        )


class CurrencyConversionFailedError(CurrencyError):
    """Raised when currency conversion fails"""
    
    def __init__(self, from_currency: str, to_currency: str, amount: float = None):
        super().__init__(
            error=f"Unable to convert {from_currency} to {to_currency} at this time",
            error_code="CURRENCY_CONVERSION_FAILED",
            details={
                "fromCurrency": from_currency,
                "toCurrency": to_currency,
                "amount": amount
            }
        )


class CurrencyRatesFetchFailedError(CurrencyError):
    """Raised when fetching currency rates fails"""
    
    def __init__(self, base_currency: str = "USD"):
        super().__init__(
            error=f"Unable to fetch currency rates for {base_currency} at this time",
            error_code="CURRENCY_RATES_FETCH_FAILED",
            details={
                "baseCurrency": base_currency
            }
        )


class CurrencyCacheError(CurrencyError):
    """Raised when currency cache operations fail"""
    
    def __init__(self, operation: str, cache_key: str = None):
        super().__init__(
            error=f"Currency cache {operation} failed",
            error_code="CURRENCY_CACHE_ERROR",
            details={
                "operation": operation,
                "cacheKey": cache_key
            }
        )


class CurrencyValidationError(CurrencyError):
    """Raised when currency validation fails"""
    
    def __init__(self, field: str, value: Any, reason: str = None):
        error_message = f"Invalid {field}: {value}"
        if reason:
            error_message += f" - {reason}"
        
        super().__init__(
            error=error_message,
            error_code="CURRENCY_VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value),
                "reason": reason
            }
        )


class ExternalApiError(CurrencyError):
    """Raised when external currency API fails"""
    
    def __init__(self, api_url: str, status_code: int = None, response_text: str = None):
        super().__init__(
            error=f"External currency API failed: {api_url}",
            error_code="EXTERNAL_API_ERROR",
            details={
                "apiUrl": api_url,
                "statusCode": status_code,
                "responseText": response_text
            }
        )


class RedisConnectionError(CurrencyError):
    """Raised when Redis connection fails"""
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            error="Redis connection failed",
            error_code="REDIS_CONNECTION_ERROR",
            details={
                "redisUrl": redis_url
            }
        )


# Error code constants for easy reference
class CurrencyErrorCodes:
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"
    CURRENCY_SERVICE_UNAVAILABLE = "CURRENCY_SERVICE_UNAVAILABLE"
    CURRENCY_CONVERSION_FAILED = "CURRENCY_CONVERSION_FAILED"
    CURRENCY_RATES_FETCH_FAILED = "CURRENCY_RATES_FETCH_FAILED"
    CURRENCY_CACHE_ERROR = "CURRENCY_CACHE_ERROR"
    CURRENCY_VALIDATION_ERROR = "CURRENCY_VALIDATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    REDIS_CONNECTION_ERROR = "REDIS_CONNECTION_ERROR"
