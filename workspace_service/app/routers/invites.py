from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.schemas.invite import (
    InviteCreate,
    InviteResponse,
    InviteListResponse,
)
from app.services.invite import InviteService
from app.services.workspace import WorkspaceService
from app.dependencies import get_invite_service, get_current_user_id
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteAlreadyUsedError,
    InvalidInviteTokenError,
    MemberAlreadyExistsError,
)

router = APIRouter(tags=["Invites"])


@router.post(
    "/workspaces/{workspace_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invite",
    description="Create an invite to a workspace. Only owners and admins can create invites.",
    responses={
        201: {"description": "Invite created successfully"},
        400: {"description": "Validation error or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
        409: {"description": "User is already a member"},
    },
)
def create_invite(
    workspace_id: UUID,
    data: InviteCreate,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteResponse:
    """Create an invite to a workspace."""
    invite, plain_token = service.create_invite(workspace_id, user_id, data)
    response = InviteResponse.model_validate(invite)
    response.invite_token = plain_token  # Include token only on creation
    return response


@router.get(
    "/workspaces/{workspace_id}/invites",
    response_model=InviteListResponse,
    summary="List workspace invites",
    description="Get all pending invites for a workspace.",
    responses={
        200: {"description": "Invites retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def list_invites(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteListResponse:
    """Get all pending invites for a workspace."""
    invites = service.get_workspace_invites(workspace_id, user_id)
    return InviteListResponse(
        invites=[InviteResponse.model_validate(i) for i in invites],
        total=len(invites),
    )


@router.delete(
    "/workspaces/{workspace_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invite",
    description="Revoke a pending invite. Only owners and admins can revoke invites.",
    responses={
        204: {"description": "Invite revoked successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace or invite not found"},
        410: {"description": "Invite already used"},
    },
)
def revoke_invite(
    workspace_id: UUID,
    invite_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> None:
    """Revoke a pending invite."""
    service.revoke_invite(workspace_id, invite_id, user_id)


@router.post(
    "/invites/{token}:accept",
    response_model=InviteResponse,
    summary="Accept invite",
    description="Accept an invite using the invite token.",
    responses={
        200: {"description": "Invite accepted successfully"},
        400: {"description": "Invalid token or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied - invite for different user"},
        410: {"description": "Invite expired or already used"},
    },
)
def accept_invite(
    token: str,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> InviteResponse:
    """Accept an invite using the token."""
    invite = service.accept_invite(token, user_id)
    return InviteResponse.model_validate(invite)


@router.post(
    "/invites/{token}:decline",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Decline invite",
    description="Decline an invite using the invite token.",
    responses={
        204: {"description": "Invite declined successfully"},
        400: {"description": "Invalid token"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied - invite for different user"},
        410: {"description": "Invite expired or already used"},
    },
)
def decline_invite(
    token: str,
    user_id: int = Depends(get_current_user_id),
    service: InviteService = Depends(get_invite_service),
) -> None:
    """Decline an invite."""
    service.decline_invite(token, user_id)

