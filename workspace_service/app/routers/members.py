"""
Router for workspace member management.

- List members: Any workspace member
- Update role: Owner only
- Remove member: Owner only
"""
from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.schemas.member import (
    MemberResponse,
    MemberRoleUpdate,
    MemberListResponse,
)
from app.services.workspace import WorkspaceService
from app.dependencies import get_workspace_service, get_current_user_id

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["Members"])


@router.get(
    "",
    response_model=MemberListResponse,
    summary="List workspace members",
    description="""
    Get all active members of a workspace.
    
    **Authorization:** Any workspace member can view the member list.
    
    Response includes:
    - Member role (owner, full, read)
    - User email
    - Join date
    """,
    responses={
        200: {"description": "Members retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not a workspace member"},
        404: {"description": "Workspace not found"},
    },
)
def list_members(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> MemberListResponse:
    """
    Get all members of a workspace.
    """
    members = service.get_members(workspace_id, user_id)
    return MemberListResponse(
        members=members,
        total=len(members),
    )


@router.patch(
    "/{target_user_id}",
    response_model=MemberResponse,
    summary="Update member role (owner only)",
    description="""
    Change a member's role in the workspace.
    
    **Authorization:** Only the workspace owner can change roles.
    
    **Available roles:**
    - `read`: View workspace data only
    - `full`: View + create/update/delete workspace data
    
    **Restrictions:**
    - Cannot change the owner's role (use ownership transfer instead)
    """,
    responses={
        200: {"description": "Member role updated successfully"},
        400: {"description": "Invalid role change or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not the workspace owner"},
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
    """
    Update a member's role (owner only).
    """
    member = service.update_member_role(workspace_id, target_user_id, user_id, data)
    # Fetch user info for response
    user_info = service.user_client.get_user(target_user_id)
    return MemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        joined_at=member.joined_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
        email=user_info.email if user_info else None,
    )


@router.delete(
    "/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member (owner only)",
    description="""
    Remove a member from the workspace.
    
    **Authorization:** Only the workspace owner can remove members.
    
    **Restrictions:**
    - Cannot remove the workspace owner
    
    **After removal:**
    - Member loses access to the workspace
    - Member can be re-invited
    """,
    responses={
        204: {"description": "Member removed successfully"},
        400: {"description": "Cannot remove owner or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not the workspace owner"},
        404: {"description": "Workspace or member not found"},
    },
)
def remove_member(
    workspace_id: UUID,
    target_user_id: int,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """
    Remove a member from the workspace (owner only).
    """
    service.remove_member(workspace_id, target_user_id, user_id)
