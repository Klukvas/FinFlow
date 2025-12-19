from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.schemas.internal import (
    AuthorizeRequest,
    AuthorizeResponse,
    UserWorkspacesResponse,
    UserWorkspaceItem,
    CreatePersonalWorkspaceRequest,
    CreatePersonalWorkspaceResponse,
    DefaultWorkspaceResponse,
)
from app.models.member import MemberRole
from app.services.workspace import WorkspaceService
from app.dependencies import get_workspace_service, verify_internal_token
from app.exceptions import WorkspaceNotFoundError

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post(
    "/workspaces/{workspace_id}/authorize",
    response_model=AuthorizeResponse,
    summary="Authorize user access",
    description="Check if a user has the required role in a workspace. For use by domain services.",
    responses={
        200: {"description": "Authorization check result"},
        403: {"description": "User not authorized"},
        404: {"description": "Workspace not found"},
    },
)
async def authorize_user(
    workspace_id: UUID,
    data: AuthorizeRequest,
    service: WorkspaceService = Depends(get_workspace_service),
    _: None = Depends(verify_internal_token),
) -> AuthorizeResponse:
    """
    Check if a user has the required role in a workspace.
    Returns 200 with authorization result or 403 if not authorized.
    """
    # Check authorization
    authorized = service.authorize(workspace_id, data.user_id, data.required_role)
    role = service.get_user_role(workspace_id, data.user_id)

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have required role in workspace"
        )

    return AuthorizeResponse(
        authorized=True,
        role=role,
        workspace_id=workspace_id,
        user_id=data.user_id,
    )


@router.get(
    "/users/{user_id}/workspaces",
    response_model=UserWorkspacesResponse,
    summary="Get user workspaces",
    description="Get all workspaces for a user. For use by domain services.",
    responses={
        200: {"description": "User workspaces retrieved"},
    },
)
async def get_user_workspaces(
    user_id: int,
    service: WorkspaceService = Depends(get_workspace_service),
    _: None = Depends(verify_internal_token),
) -> UserWorkspacesResponse:
    """Get all workspaces for a user (internal endpoint)."""
    workspaces = service.get_user_workspaces(user_id, include_archived=False)
    default_workspace = service.get_user_default_workspace(user_id)

    items = []
    for ws in workspaces:
        role = service.get_user_role(ws.id, user_id)
        items.append(UserWorkspaceItem(
            id=ws.id,
            name=ws.name,
            role=role,
            type=ws.type.value,
            is_default=(default_workspace and ws.id == default_workspace.id),
        ))

    return UserWorkspacesResponse(workspaces=items)


@router.get(
    "/users/{user_id}/default-workspace",
    response_model=DefaultWorkspaceResponse,
    summary="Get user's default workspace",
    description="Get the default (personal) workspace for a user. For use by domain services.",
    responses={
        200: {"description": "Default workspace retrieved"},
        404: {"description": "No default workspace found"},
    },
)
async def get_user_default_workspace(
    user_id: int,
    service: WorkspaceService = Depends(get_workspace_service),
    _: None = Depends(verify_internal_token),
) -> DefaultWorkspaceResponse:
    """Get user's default workspace (internal endpoint)."""
    workspace = service.get_user_default_workspace(user_id)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default workspace found for user"
        )

    return DefaultWorkspaceResponse(
        workspace_id=workspace.id,
        name=workspace.name,
        type=workspace.type.value,
    )


@router.post(
    "/workspaces/personal",
    response_model=CreatePersonalWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create personal workspace",
    description="Create a personal workspace for a new user during registration. For use by user_service.",
    responses={
        201: {"description": "Personal workspace created"},
        400: {"description": "Failed to create workspace"},
    },
)
async def create_personal_workspace(
    data: CreatePersonalWorkspaceRequest,
    service: WorkspaceService = Depends(get_workspace_service),
    _: None = Depends(verify_internal_token),
) -> CreatePersonalWorkspaceResponse:
    """
    Create a personal workspace for a new user.
    Called by user_service during registration.
    """
    workspace = service.create_personal_workspace(data.user_id)
    return CreatePersonalWorkspaceResponse(workspace_id=workspace.id)


@router.get(
    "/workspaces/{workspace_id}/role/{user_id}",
    summary="Get user role in workspace",
    description="Get the role of a specific user in a workspace. For use by domain services.",
    responses={
        200: {"description": "User role retrieved"},
        404: {"description": "User is not a member of workspace"},
    },
)
async def get_user_role_in_workspace(
    workspace_id: UUID,
    user_id: int,
    service: WorkspaceService = Depends(get_workspace_service),
    _: None = Depends(verify_internal_token),
) -> dict:
    """Get user's role in a specific workspace (internal endpoint)."""
    role = service.get_user_role(workspace_id, user_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not an active member of this workspace"
        )

    return {
        "workspace_id": str(workspace_id),
        "user_id": user_id,
        "role": role.value,
    }

