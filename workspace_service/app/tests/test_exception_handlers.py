"""
Unit tests for exception-to-response mapping handlers.

Tests cover:
- custom_validation_exception_handler (multiple error types)
- All workspace-specific exception handlers
- http_exception_handler for generic HTTP exceptions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST

from app.exception_handlers import (
    custom_validation_exception_handler,
    workspace_not_found_handler,
    workspace_validation_handler,
    workspace_access_denied_handler,
    workspace_archived_handler,
    member_not_found_handler,
    member_already_exists_handler,
    invalid_role_change_handler,
    owner_cannot_leave_handler,
    invite_not_found_handler,
    invite_expired_handler,
    invite_already_used_handler,
    invite_not_actionable_handler,
    invitee_not_found_handler,
    self_invite_not_allowed_handler,
    personal_workspace_protected_handler,
    http_exception_handler,
)
from app.exceptions.workspace_errors import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
    InvalidRoleChangeError,
    OwnerCannotLeaveError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteAlreadyUsedError,
    InviteNotActionableError,
    InviteeNotFoundError,
    SelfInviteNotAllowedError,
    PersonalWorkspaceProtectedError,
    WorkspaceErrorCode,
)


def _mock_request() -> MagicMock:
    """Create a minimal mock Request."""
    return MagicMock(spec=Request)


# ==================== Validation Handler ====================


class TestCustomValidationExceptionHandler:
    """Tests for custom_validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_empty_errors_list(self):
        """Return generic validation error when errors list is empty."""
        exc = RequestValidationError(errors=[])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        assert resp.status_code == HTTP_400_BAD_REQUEST
        body = resp.body.decode()
        assert "Validation error" in body

    @pytest.mark.asyncio
    async def test_missing_field(self):
        """Format 'missing' error type correctly."""
        exc = RequestValidationError(errors=[
            {"loc": ("body", "name"), "type": "missing", "msg": "Field required"}
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        assert resp.status_code == HTTP_400_BAD_REQUEST
        body = resp.body.decode()
        assert "Name" in body
        assert "required" in body.lower()

    @pytest.mark.asyncio
    async def test_string_too_short(self):
        """Format 'string_too_short' error type with min_length."""
        exc = RequestValidationError(errors=[
            {
                "loc": ("body", "name"),
                "type": "string_too_short",
                "msg": "String should have at least 1 character",
                "ctx": {"min_length": 1},
            }
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        body = resp.body.decode()
        assert "Name" in body
        assert "1" in body

    @pytest.mark.asyncio
    async def test_string_too_long(self):
        """Format 'string_too_long' error type with max_length."""
        exc = RequestValidationError(errors=[
            {
                "loc": ("body", "description"),
                "type": "string_too_long",
                "msg": "String should have at most 255 characters",
                "ctx": {"max_length": 255},
            }
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        body = resp.body.decode()
        assert "Description" in body
        assert "255" in body

    @pytest.mark.asyncio
    async def test_value_error(self):
        """Use original message for 'value_error' type."""
        exc = RequestValidationError(errors=[
            {
                "loc": ("body", "email"),
                "type": "value_error",
                "msg": "Invalid email format",
            }
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        body = resp.body.decode()
        assert "Invalid email format" in body

    @pytest.mark.asyncio
    async def test_generic_error_type(self):
        """Use field + message for unknown error types."""
        exc = RequestValidationError(errors=[
            {
                "loc": ("body", "amount"),
                "type": "int_parsing",
                "msg": "Input should be a valid integer",
            }
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        body = resp.body.decode()
        assert "Amount" in body

    @pytest.mark.asyncio
    async def test_empty_loc(self):
        """Handle error with empty loc gracefully."""
        exc = RequestValidationError(errors=[
            {"loc": (), "type": "missing", "msg": "Field required"}
        ])
        resp = await custom_validation_exception_handler(_mock_request(), exc)
        body = resp.body.decode()
        assert "required" in body.lower()


# ==================== Workspace Exception Handlers ====================


class TestWorkspaceExceptionHandlers:
    """Tests for all workspace-specific exception handlers."""

    @pytest.mark.asyncio
    async def test_workspace_not_found_handler(self):
        ws_id = uuid4()
        exc = WorkspaceNotFoundError(workspace_id=ws_id)
        resp = await workspace_not_found_handler(_mock_request(), exc)
        assert resp.status_code == 404
        body = resp.body.decode()
        assert str(ws_id) in body
        assert WorkspaceErrorCode.WORKSPACE_NOT_FOUND in body

    @pytest.mark.asyncio
    async def test_workspace_validation_handler(self):
        exc = WorkspaceValidationError(detail="Bad data")
        resp = await workspace_validation_handler(_mock_request(), exc)
        assert resp.status_code == 400
        body = resp.body.decode()
        assert "Bad data" in body

    @pytest.mark.asyncio
    async def test_workspace_access_denied_handler(self):
        exc = WorkspaceAccessDeniedError()
        resp = await workspace_access_denied_handler(_mock_request(), exc)
        assert resp.status_code == 403
        body = resp.body.decode()
        assert WorkspaceErrorCode.ACCESS_DENIED in body

    @pytest.mark.asyncio
    async def test_workspace_archived_handler(self):
        exc = WorkspaceArchivedError()
        resp = await workspace_archived_handler(_mock_request(), exc)
        assert resp.status_code == 400
        body = resp.body.decode()
        assert "archived" in body.lower()

    @pytest.mark.asyncio
    async def test_member_not_found_handler(self):
        exc = MemberNotFoundError(user_id=5)
        resp = await member_not_found_handler(_mock_request(), exc)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_member_already_exists_handler(self):
        exc = MemberAlreadyExistsError(user_id=5, workspace_id=uuid4())
        resp = await member_already_exists_handler(_mock_request(), exc)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_role_change_handler(self):
        exc = InvalidRoleChangeError()
        resp = await invalid_role_change_handler(_mock_request(), exc)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_owner_cannot_leave_handler(self):
        exc = OwnerCannotLeaveError()
        resp = await owner_cannot_leave_handler(_mock_request(), exc)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invite_not_found_handler(self):
        exc = InviteNotFoundError()
        resp = await invite_not_found_handler(_mock_request(), exc)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invite_expired_handler(self):
        exc = InviteExpiredError()
        resp = await invite_expired_handler(_mock_request(), exc)
        assert resp.status_code == 410

    @pytest.mark.asyncio
    async def test_invite_already_used_handler(self):
        exc = InviteAlreadyUsedError()
        resp = await invite_already_used_handler(_mock_request(), exc)
        assert resp.status_code == 410

    @pytest.mark.asyncio
    async def test_invite_not_actionable_handler(self):
        exc = InviteNotActionableError()
        resp = await invite_not_actionable_handler(_mock_request(), exc)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invitee_not_found_handler(self):
        exc = InviteeNotFoundError(email="ghost@example.com")
        resp = await invitee_not_found_handler(_mock_request(), exc)
        assert resp.status_code == 404
        assert "ghost@example.com" in resp.body.decode()

    @pytest.mark.asyncio
    async def test_self_invite_not_allowed_handler(self):
        exc = SelfInviteNotAllowedError()
        resp = await self_invite_not_allowed_handler(_mock_request(), exc)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_personal_workspace_protected_handler(self):
        exc = PersonalWorkspaceProtectedError()
        resp = await personal_workspace_protected_handler(_mock_request(), exc)
        assert resp.status_code == 400


class TestHttpExceptionHandler:
    """Tests for the generic http_exception_handler."""

    @pytest.mark.asyncio
    async def test_generic_http_exception(self):
        exc = HTTPException(status_code=500, detail="Something broke")
        resp = await http_exception_handler(_mock_request(), exc)
        assert resp.status_code == 500
        body = resp.body.decode()
        assert "Something broke" in body
        assert WorkspaceErrorCode.INTERNAL_ERROR in body

    @pytest.mark.asyncio
    async def test_http_401(self):
        exc = HTTPException(status_code=401, detail="Unauthorized")
        resp = await http_exception_handler(_mock_request(), exc)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_has_error_and_errorcode(self):
        exc = HTTPException(status_code=403, detail="Forbidden")
        resp = await http_exception_handler(_mock_request(), exc)
        import json
        body = json.loads(resp.body.decode())
        assert "error" in body
        assert "errorCode" in body
