"""Tests for custom exceptions."""

from app.exceptions import (
    InsufficientDataError,
    LLMServiceError,
    LLMRateLimitError,
    FeatureNotAvailableError,
    CooldownActiveError,
)


class TestInsufficientDataError:
    def test_default_message(self):
        exc = InsufficientDataError()
        assert exc.status_code == 422
        assert exc.detail["errorCode"] == "INSUFFICIENT_DATA"
        assert "Not enough" in exc.detail["error"]

    def test_custom_message(self):
        exc = InsufficientDataError("Need more expenses")
        assert exc.detail["error"] == "Need more expenses"


class TestLLMServiceError:
    def test_default_message(self):
        exc = LLMServiceError()
        assert exc.status_code == 503
        assert exc.detail["errorCode"] == "LLM_SERVICE_ERROR"

    def test_custom_message(self):
        exc = LLMServiceError("API timeout")
        assert exc.detail["error"] == "API timeout"


class TestLLMRateLimitError:
    def test_default_message(self):
        exc = LLMRateLimitError()
        assert exc.status_code == 429
        assert exc.detail["errorCode"] == "LLM_RATE_LIMITED"


class TestFeatureNotAvailableError:
    def test_default_message(self):
        exc = FeatureNotAvailableError()
        assert exc.status_code == 402
        assert exc.detail["errorCode"] == "FEATURE_NOT_AVAILABLE"
        assert "Professional" in exc.detail["error"]


class TestCooldownActiveError:
    def test_with_retry_after(self):
        exc = CooldownActiveError(retry_after=3600)
        assert exc.status_code == 429
        assert exc.detail["errorCode"] == "COOLDOWN_ACTIVE"
        assert exc.detail["retry_after"] == 3600

    def test_custom_message(self):
        exc = CooldownActiveError(retry_after=7200, message="Wait 2 hours")
        assert exc.detail["error"] == "Wait 2 hours"
        assert exc.detail["retry_after"] == 7200
