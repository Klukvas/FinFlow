"""
Router for workspace invite management (owner operations).

These endpoints are for the workspace owner to:
- Create invites (by email)
- List pending invites for their workspace
- Cancel pending invites
"""
from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from typing import Optional

from app.schemas.invite import (
    InviteCreate,
    InviteResponse,
    InviteListResponse,
)
from app.models.invite import InviteStatus
from app.services.invite import InviteService
from app.dependencies import get_invite_service, get_current_user_id

router = APIRouter(tags=["Workspace Invites"])


@router.post(
    "/workspaces/{workspace_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invite (owner only)",
    description="""
    Create an invitation to share a workspace with another user.
    
    **Authorization:** Only the workspace owner can create invites.
    
    **Business Rules:**
    - Invitee must be an existing user (looked up by email)
    - Cannot invite yourself
    - Cannot invite someone who is already a member
    - If a PENDING invite already exists for this user, returns the existing invite
    - If previous invite was EXPIRED/REJECTED/CANCELED, creates a new one
    - Invites expire after 3 days
    
    **Roles:**
    - `read`: View workspace data only
    - `full`: View + create/update/delete workspace data
    """,
    responses={
        201: {"description": "Invite created successfully"},
        200: {"description": "Existing pending invite returned"},
        400: {"description": "Validation error, self-invite, or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not the workspace owner"},
        404: {"description": "Workspace not found or invitee email not found"},
        409: {"description": "User is already a member"},
    },
)
def create_invite(
    workspace_id: UUID,
    data: InviteCreate,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteResponse:
    """
    Create an invite to share the workspace with another user.
    """
    invite, is_new = service.create_invite(workspace_id, user_id, data)
    response = InviteResponse.model_validate(invite)
    # Note: We return 201 for both new and existing invites for simplicity
    # Frontend can check the created_at timestamp to determine if it's new
    return response


@router.get(
    "/workspaces/{workspace_id}/invites",
    response_model=InviteListResponse,
    summary="List workspace invites (owner only)",
    description="""
    Get all invites for a workspace.
    
    **Authorization:** Only the workspace owner can view invites.
    
    By default, returns only PENDING invites.
    Use the `status` parameter to filter by specific status.
    """,
    responses={
        200: {"description": "Invites retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not the workspace owner"},
        404: {"description": "Workspace not found"},
    },
)
def list_invites(
    workspace_id: UUID,
    status_filter: Optional[InviteStatus] = Query(
        None,
        alias="status",
        description="Filter by invite status (defaults to pending)"
    ),
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteListResponse:
    """
    Get all invites for a workspace (owner only).
    """
    invites = service.get_workspace_invites(workspace_id, user_id, status_filter)
    return InviteListResponse(
        invites=[InviteResponse.model_validate(i) for i in invites],
        total=len(invites),
    )


@router.delete(
    "/workspaces/{workspace_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel invite (owner only)",
    description="""
    Cancel a pending invitation.
    
    **Authorization:** Only the workspace owner can cancel invites.
    
    Only PENDING invites can be canceled.
    Once canceled, a new invite can be sent to the same user.
    """,
    responses={
        204: {"description": "Invite canceled successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not the workspace owner"},
        404: {"description": "Workspace or invite not found"},
        410: {"description": "Invite already used/expired/canceled"},
    },
)
def cancel_invite(
    workspace_id: UUID,
    invite_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> None:
    """
    Cancel a pending invite (owner only).
    """
    service.cancel_invite(workspace_id, invite_id, user_id)
