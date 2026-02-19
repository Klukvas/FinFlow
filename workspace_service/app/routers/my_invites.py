"""
Router for invitee's incoming invites.

Endpoints for users to view and respond to workspace invitations they've received.
"""
from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from typing import Optional

from app.schemas.invite import MyInviteResponse, MyInviteListResponse, InviteResponse
from app.services.invite import InviteService
from app.dependencies import get_invite_service, get_current_user_id

router = APIRouter(prefix="/me/invites", tags=["My Invites"])


@router.get(
    "",
    response_model=MyInviteListResponse,
    summary="List my incoming invites",
    description="""
    Get all workspace invitations sent to the current user.
    
    By default, only shows PENDING invites.
    Use `include_all=true` to include accepted/rejected/expired invites.
    
    Response includes rich information:
    - Workspace name
    - Inviter's email
    - Role that will be assigned
    - Expiration status
    """,
    responses={
        200: {"description": "Invites retrieved successfully"},
        401: {"description": "Unauthorized"},
    },
)
def list_my_invites(
    include_all: bool = Query(
        False,
        description="Include non-pending invites (accepted, rejected, expired, canceled)"
    ),
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> MyInviteListResponse:
    """
    List all workspace invitations for the current user.
    
    This is used by the "My Invites" tab in the frontend.
    """
    invites = service.get_my_invites(user_id, include_all=include_all)
    return MyInviteListResponse(
        invites=invites,
        total=len(invites),
    )


@router.post(
    "/{invite_id}:accept",
    response_model=InviteResponse,
    summary="Accept invite",
    description="""
    Accept a workspace invitation.
    
    - Only the invitee can accept
    - Invite must be PENDING and not expired
    - Creates membership with the role specified in the invite
    - After acceptance, user can access the workspace
    """,
    responses={
        200: {"description": "Invite accepted, membership created"},
        400: {"description": "Invite cannot be accepted (not actionable)"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not your invite"},
        404: {"description": "Invite not found"},
        410: {"description": "Invite expired"},
    },
)
def accept_invite(
    invite_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteResponse:
    """
    Accept a workspace invitation.
    
    The user will be added as a member with the role specified in the invite.
    """
    invite = service.accept_invite(invite_id, user_id)
    return InviteResponse.model_validate(invite)


@router.post(
    "/{invite_id}:reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject invite",
    description="""
    Reject a workspace invitation.
    
    - Only the invitee can reject
    - Invite must be PENDING and not expired
    - After rejection, the owner can send a new invite
    """,
    responses={
        204: {"description": "Invite rejected successfully"},
        400: {"description": "Invite cannot be rejected (not actionable)"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not your invite"},
        404: {"description": "Invite not found"},
        410: {"description": "Invite expired"},
    },
)
def reject_invite(
    invite_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> None:
    """
    Reject a workspace invitation.
    """
    service.reject_invite(invite_id, user_id)
