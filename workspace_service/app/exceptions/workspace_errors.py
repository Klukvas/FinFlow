from fastapi import HTTPException, status
from typing import Optional
from enum import Enum
from uuid import UUID


class WorkspaceServiceError(str, Enum):
    WORKSPACE_NOT_FOUND = "Workspace not found"
    WORKSPACE_ARCHIVED = "Workspace is archived"
    ACCESS_DENIED = "Access denied to workspace"
    MEMBER_NOT_FOUND = "Member not found"
    MEMBER_ALREADY_EXISTS = "User is already a member of this workspace"
    INVALID_ROLE_CHANGE = "Invalid role change"
    OWNER_CANNOT_LEAVE = "Owner cannot leave workspace without transferring ownership"
    INVITE_NOT_FOUND = "Invite not found"
    INVITE_EXPIRED = "Invite has expired"
    INVITE_ALREADY_USED = "Invite has already been used"
    INVALID_INVITE_TOKEN = "Invalid invite token"
    VALIDATION_ERROR = "Validation error"


class WorkspaceErrorCode(str, Enum):
    WORKSPACE_NOT_FOUND = "WORKSPACE_NOT_FOUND"
    WORKSPACE_ARCHIVED = "WORKSPACE_ARCHIVED"
    ACCESS_DENIED = "ACCESS_DENIED"
    MEMBER_NOT_FOUND = "MEMBER_NOT_FOUND"
    MEMBER_ALREADY_EXISTS = "MEMBER_ALREADY_EXISTS"
    INVALID_ROLE_CHANGE = "INVALID_ROLE_CHANGE"
    OWNER_CANNOT_LEAVE = "OWNER_CANNOT_LEAVE"
    INVITE_NOT_FOUND = "INVITE_NOT_FOUND"
    INVITE_EXPIRED = "INVITE_EXPIRED"
    INVITE_ALREADY_USED = "INVITE_ALREADY_USED"
    INVALID_INVITE_TOKEN = "INVALID_INVITE_TOKEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WorkspaceNotFoundError(HTTPException):
    def __init__(self, workspace_id: Optional[UUID] = None, detail: Optional[str] = None):
        if detail is None:
            detail = f"Workspace with ID {workspace_id} not found" if workspace_id else "Workspace not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.WORKSPACE_NOT_FOUND


class WorkspaceValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.VALIDATION_ERROR


class WorkspaceAccessDeniedError(HTTPException):
    def __init__(self, detail: str = "Access denied to this workspace"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.ACCESS_DENIED


class WorkspaceArchivedError(HTTPException):
    def __init__(self, workspace_id: Optional[UUID] = None):
        detail = f"Workspace {workspace_id} is archived" if workspace_id else "Workspace is archived"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.WORKSPACE_ARCHIVED


class MemberNotFoundError(HTTPException):
    def __init__(self, user_id: Optional[int] = None, workspace_id: Optional[UUID] = None):
        if user_id and workspace_id:
            detail = f"User {user_id} is not a member of workspace {workspace_id}"
        elif user_id:
            detail = f"Member with user ID {user_id} not found"
        else:
            detail = "Member not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.MEMBER_NOT_FOUND


class MemberAlreadyExistsError(HTTPException):
    def __init__(self, user_id: int, workspace_id: UUID):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {user_id} is already a member of workspace {workspace_id}"
        )
        self.error_code = WorkspaceErrorCode.MEMBER_ALREADY_EXISTS


class InvalidRoleChangeError(HTTPException):
    def __init__(self, detail: str = "Invalid role change"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.INVALID_ROLE_CHANGE


class OwnerCannotLeaveError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave workspace without transferring ownership first"
        )
        self.error_code = WorkspaceErrorCode.OWNER_CANNOT_LEAVE


class InviteNotFoundError(HTTPException):
    def __init__(self, invite_id: Optional[UUID] = None):
        detail = f"Invite {invite_id} not found" if invite_id else "Invite not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        self.error_code = WorkspaceErrorCode.INVITE_NOT_FOUND


class InviteExpiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail="This invite has expired"
        )
        self.error_code = WorkspaceErrorCode.INVITE_EXPIRED


class InviteAlreadyUsedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail="This invite has already been used"
        )
        self.error_code = WorkspaceErrorCode.INVITE_ALREADY_USED


class InvalidInviteTokenError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite token"
        )
        self.error_code = WorkspaceErrorCode.INVALID_INVITE_TOKEN

