from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.schemas.member import (
    MemberResponse,
    MemberRoleUpdate,
    MemberListResponse,
)
from app.services.workspace import WorkspaceService
from app.dependencies import get_workspace_service, get_current_user_id
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    MemberNotFoundError,
    InvalidRoleChangeError,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["Members"])


@router.get(
    "",
    response_model=MemberListResponse,
    summary="List workspace members",
    description="Get all active members of a workspace.",
    responses={
        200: {"description": "Members retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def list_members(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> MemberListResponse:
    """Get all members of a workspace."""
    members = service.get_members(workspace_id, user_id)
    return MemberListResponse(
        members=[MemberResponse.model_validate(m) for m in members],
        total=len(members),
    )


@router.patch(
    "/{target_user_id}",
    response_model=MemberResponse,
    summary="Update member role",
    description="Update a member's role. Only owners and admins can update roles.",
    responses={
        200: {"description": "Member role updated successfully"},
        400: {"description": "Invalid role change or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace or member not found"},
    },
)
def update_member_role(
    workspace_id: UUID,
    target_user_id: int,
    data: MemberRoleUpdate,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> MemberResponse:
    """Update a member's role."""
    member = service.update_member_role(workspace_id, target_user_id, user_id, data)
    return MemberResponse.model_validate(member)


@router.delete(
    "/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="Remove a member from the workspace. Only owners and admins can remove members.",
    responses={
        204: {"description": "Member removed successfully"},
        400: {"description": "Cannot remove owner or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace or member not found"},
    },
)
def remove_member(
    workspace_id: UUID,
    target_user_id: int,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """Remove a member from the workspace."""
    service.remove_member(workspace_id, target_user_id, user_id)

