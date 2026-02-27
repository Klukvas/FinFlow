from fastapi import HTTPException
from typing import Optional


class InsufficientDataError(HTTPException):
    def __init__(self, message: str = "Not enough financial data for analysis"):
        super().__init__(
            status_code=422,
            detail={
                "error": message,
                "errorCode": "INSUFFICIENT_DATA",
            },
        )


class LLMServiceError(HTTPException):
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(
            status_code=503,
            detail={
                "error": message,
                "errorCode": "LLM_SERVICE_ERROR",
            },
        )


class LLMRateLimitError(HTTPException):
    def __init__(self, message: str = "AI service rate limit exceeded, please try again later"):
        super().__init__(
            status_code=503,
            detail={
                "error": message,
                "errorCode": "LLM_RATE_LIMITED",
            },
        )


class FeatureNotAvailableError(HTTPException):
    def __init__(self, message: str = "AI assistant requires Professional or Enterprise plan"):
        super().__init__(
            status_code=402,
            detail={
                "error": message,
                "errorCode": "FEATURE_NOT_AVAILABLE",
            },
        )


class QuotaExhaustedError(HTTPException):
    def __init__(self, retry_after: int, message: Optional[str] = None):
        super().__init__(
            status_code=429,
            detail={
                "error": message or "Monthly AI analysis quota exhausted",
                "errorCode": "QUOTA_EXHAUSTED",
                "retry_after": retry_after,
            },
        )


# Keep backward-compatible alias
CooldownActiveError = QuotaExhaustedError
