"""Tests for error classes and handlers."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.utils.errors import (
    ServiceError,
    NotFoundError,
    ValidationError,
    ConflictError,
    AuthError,
    error_response,
    service_exception_handler,
    unhandled_exception_handler,
)


class TestServiceError:
    """Tests for ServiceError hierarchy."""

    def test_default_error_code_and_status(self):
        error = ServiceError("Something broke")
        assert error.error_code == "@subscription_service/INTERNAL_ERROR"
        assert error.status_code == 500
        assert error.message == "Something broke"

    def test_custom_error_code_and_status(self):
        error = ServiceError(
            "Custom error",
            error_code="@subscription_service/CUSTOM",
            status_code=418,
        )
        assert error.error_code == "@subscription_service/CUSTOM"
        assert error.status_code == 418

    def test_not_found_error_defaults(self):
        error = NotFoundError("Not found")
        assert error.status_code == 404

    def test_validation_error_defaults(self):
        error = ValidationError("Bad input")
        assert error.status_code == 400

    def test_conflict_error_defaults(self):
        error = ConflictError("Conflict")
        assert error.status_code == 409

    def test_auth_error_defaults(self):
        error = AuthError("Unauthorized")
        assert error.status_code == 401

    def test_subclass_custom_error_code(self):
        error = NotFoundError(
            "User not found",
            error_code="@subscription_service/USER_NOT_FOUND",
        )
        assert error.error_code == "@subscription_service/USER_NOT_FOUND"
        assert error.status_code == 404


class TestErrorResponse:
    """Tests for error_response helper."""

    def test_returns_json_response(self):
        resp = error_response("Test error", "@test/ERROR", 422)
        assert resp.status_code == 422
        # body should contain error and errorCode

    def test_correct_content(self):
        resp = error_response("Not found", "@test/NOT_FOUND", 404)
        assert resp.status_code == 404


class TestExceptionHandlers:
    """Tests for exception handler functions."""

    @pytest.mark.asyncio
    async def test_service_exception_handler(self):
        request = MagicMock()
        request.url.path = "/v1/test"
        exc = NotFoundError("Not found", error_code="@test/NOT_FOUND")

        resp = await service_exception_handler(request, exc)

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler(self):
        request = MagicMock()
        request.url.path = "/v1/test"
        exc = RuntimeError("unexpected")

        resp = await unhandled_exception_handler(request, exc)

        assert resp.status_code == 500
