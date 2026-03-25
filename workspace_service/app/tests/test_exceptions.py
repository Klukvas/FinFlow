"""
Unit tests for workspace exception classes.

Tests cover:
- WorkspaceServiceError enum values
- WorkspaceErrorCode enum values
- All custom HTTPException subclasses: status codes, details, error codes
"""
import pytest
from uuid import uuid4, UUID
from fastapi import status

from app.exceptions.workspace_errors import (
    WorkspaceServiceError,
    WorkspaceErrorCode,
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
    WorkspaceLimitExceededError,
    WorkspaceReadOnlyExcessError,
)


class TestWorkspaceServiceErrorEnum:
    """Tests for WorkspaceServiceError enum."""

    def test_all_error_messages_are_strings(self):
        """All enum values should be human-readable strings."""
        for member in WorkspaceServiceError:
            assert isinstance(member.value, str)
            assert len(member.value) > 0

    def test_workspace_not_found_value(self):
        assert WorkspaceServiceError.WORKSPACE_NOT_FOUND == "Workspace not found"

    def test_access_denied_value(self):
        assert WorkspaceServiceError.ACCESS_DENIED == "Access denied to workspace"

    def test_self_invite_not_allowed_value(self):
        assert WorkspaceServiceError.SELF_INVITE_NOT_ALLOWED == "Cannot invite yourself"


class TestWorkspaceErrorCodeEnum:
    """Tests for WorkspaceErrorCode enum."""

    def test_all_codes_are_uppercase_strings(self):
        """All error codes should be uppercase identifiers."""
        for member in WorkspaceErrorCode:
            assert isinstance(member.value, str)
            assert member.value == member.value.upper()

    def test_has_internal_error(self):
        assert WorkspaceErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"

    def test_has_validation_error(self):
        assert WorkspaceErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"


class TestWorkspaceNotFoundError:
    """Tests for WorkspaceNotFoundError."""

    def test_with_workspace_id(self):
        ws_id = uuid4()
        exc = WorkspaceNotFoundError(workspace_id=ws_id)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert str(ws_id) in exc.detail
        assert exc.error_code == WorkspaceErrorCode.WORKSPACE_NOT_FOUND

    def test_without_workspace_id(self):
        exc = WorkspaceNotFoundError()
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == "Workspace not found"
        assert exc.error_code == WorkspaceErrorCode.WORKSPACE_NOT_FOUND

    def test_with_custom_detail(self):
        exc = WorkspaceNotFoundError(detail="Custom message")
        assert exc.detail == "Custom message"
        assert exc.status_code == status.HTTP_404_NOT_FOUND


class TestWorkspaceValidationError:
    """Tests for WorkspaceValidationError."""

    def test_basic(self):
        exc = WorkspaceValidationError(detail="Name too long")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.detail == "Name too long"
        assert exc.error_code == WorkspaceErrorCode.VALIDATION_ERROR


class TestWorkspaceAccessDeniedError:
    """Tests for WorkspaceAccessDeniedError."""

    def test_default_detail(self):
        exc = WorkspaceAccessDeniedError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert "Access denied" in exc.detail
        assert exc.error_code == WorkspaceErrorCode.ACCESS_DENIED

    def test_custom_detail(self):
        exc = WorkspaceAccessDeniedError(detail="You are not allowed")
        assert exc.detail == "You are not allowed"


class TestWorkspaceArchivedError:
    """Tests for WorkspaceArchivedError."""

    def test_with_workspace_id(self):
        ws_id = uuid4()
        exc = WorkspaceArchivedError(workspace_id=ws_id)
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert str(ws_id) in exc.detail
        assert exc.error_code == WorkspaceErrorCode.WORKSPACE_ARCHIVED

    def test_without_workspace_id(self):
        exc = WorkspaceArchivedError()
        assert "archived" in exc.detail.lower()


class TestMemberNotFoundError:
    """Tests for MemberNotFoundError."""

    def test_with_both_ids(self):
        exc = MemberNotFoundError(user_id=42, workspace_id=uuid4())
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "42" in exc.detail
        assert exc.error_code == WorkspaceErrorCode.MEMBER_NOT_FOUND

    def test_with_user_id_only(self):
        exc = MemberNotFoundError(user_id=42)
        assert "42" in exc.detail

    def test_with_no_ids(self):
        exc = MemberNotFoundError()
        assert exc.detail == "Member not found"


class TestMemberAlreadyExistsError:
    """Tests for MemberAlreadyExistsError."""

    def test_basic(self):
        ws_id = uuid4()
        exc = MemberAlreadyExistsError(user_id=7, workspace_id=ws_id)
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert "7" in exc.detail
        assert str(ws_id) in exc.detail
        assert exc.error_code == WorkspaceErrorCode.MEMBER_ALREADY_EXISTS


class TestInvalidRoleChangeError:
    """Tests for InvalidRoleChangeError."""

    def test_default_detail(self):
        exc = InvalidRoleChangeError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.detail == "Invalid role change"
        assert exc.error_code == WorkspaceErrorCode.INVALID_ROLE_CHANGE

    def test_custom_detail(self):
        exc = InvalidRoleChangeError(detail="Cannot demote owner")
        assert exc.detail == "Cannot demote owner"


class TestOwnerCannotLeaveError:
    """Tests for OwnerCannotLeaveError."""

    def test_basic(self):
        exc = OwnerCannotLeaveError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "transfer" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.OWNER_CANNOT_LEAVE


class TestInviteNotFoundError:
    """Tests for InviteNotFoundError."""

    def test_with_id(self):
        inv_id = uuid4()
        exc = InviteNotFoundError(invite_id=inv_id)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert str(inv_id) in exc.detail
        assert exc.error_code == WorkspaceErrorCode.INVITE_NOT_FOUND

    def test_without_id(self):
        exc = InviteNotFoundError()
        assert exc.detail == "Invite not found"


class TestInviteExpiredError:
    """Tests for InviteExpiredError."""

    def test_basic(self):
        exc = InviteExpiredError()
        assert exc.status_code == status.HTTP_410_GONE
        assert "expired" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.INVITE_EXPIRED


class TestInviteAlreadyUsedError:
    """Tests for InviteAlreadyUsedError."""

    def test_basic(self):
        exc = InviteAlreadyUsedError()
        assert exc.status_code == status.HTTP_410_GONE
        assert "already been used" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.INVITE_ALREADY_USED


class TestInviteNotActionableError:
    """Tests for InviteNotActionableError."""

    def test_default_detail(self):
        exc = InviteNotActionableError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be accepted or rejected" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.INVITE_NOT_ACTIONABLE

    def test_custom_detail(self):
        exc = InviteNotActionableError(detail="Already handled")
        assert exc.detail == "Already handled"


class TestInviteeNotFoundError:
    """Tests for InviteeNotFoundError."""

    def test_basic(self):
        exc = InviteeNotFoundError(email="nobody@example.com")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "nobody@example.com" in exc.detail
        assert exc.error_code == WorkspaceErrorCode.INVITEE_NOT_FOUND


class TestSelfInviteNotAllowedError:
    """Tests for SelfInviteNotAllowedError."""

    def test_basic(self):
        exc = SelfInviteNotAllowedError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "yourself" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.SELF_INVITE_NOT_ALLOWED


class TestPersonalWorkspaceProtectedError:
    """Tests for PersonalWorkspaceProtectedError."""

    def test_default_detail(self):
        exc = PersonalWorkspaceProtectedError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "personal workspace" in exc.detail.lower()
        assert exc.error_code == WorkspaceErrorCode.PERSONAL_WORKSPACE_PROTECTED

    def test_custom_detail(self):
        exc = PersonalWorkspaceProtectedError(detail="Cannot archive personal")
        assert exc.detail == "Cannot archive personal"


class TestWorkspaceLimitExceededError:
    """Tests for WorkspaceLimitExceededError."""

    def test_basic(self):
        exc = WorkspaceLimitExceededError(current_count=5, limit=3)
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert "5" in exc.detail
        assert "3" in exc.detail
        assert exc.error_code == WorkspaceErrorCode.WORKSPACE_LIMIT_EXCEEDED
        assert exc.current_count == 5
        assert exc.limit == 3


class TestWorkspaceReadOnlyExcessError:
    """Tests for WorkspaceReadOnlyExcessError."""

    def test_basic(self):
        ws_id = uuid4()
        exc = WorkspaceReadOnlyExcessError(workspace_id=ws_id, current_count=4, limit=2)
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == WorkspaceErrorCode.WORKSPACE_LIMIT_EXCEEDED
        # detail is a dict for this exception
        assert exc.detail["current_count"] == 4
        assert exc.detail["limit"] == 2
        assert exc.detail["errorCode"] == "RECORD_READ_ONLY_EXCESS"
