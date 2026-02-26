from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID

from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
)
from app.services.workspace import WorkspaceService
from app.dependencies import get_workspace_service, get_current_user_id
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
    description="Create a new workspace. The authenticated user becomes the owner.",
    responses={
        201: {"description": "Workspace created successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
    },
)
def create_workspace(
    data: WorkspaceCreate,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Create a new workspace."""
    workspace = service.create_workspace(user_id, data)
    return service.get_workspace_response(workspace, user_id)


@router.get(
    "",
    response_model=WorkspaceListResponse,
    summary="List user workspaces",
    description="Get all workspaces the authenticated user is a member of.",
    responses={
        200: {"description": "Workspaces retrieved successfully"},
        401: {"description": "Unauthorized"},
    },
)
def list_workspaces(
    include_archived: bool = False,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceListResponse:
    """Get all workspaces for the current user."""
    workspaces = service.get_user_workspaces(user_id, include_archived)

    items = [service.get_workspace_response(w, user_id) for w in workspaces]

    ordered_ids = service._get_ordered_ids(user_id)
    read_only_ids = service.subscription_client.get_read_only_ids(user_id, "workspaces", ordered_ids)
    for item in items:
        item.is_read_only = item.id in read_only_ids

    return WorkspaceListResponse(
        workspaces=items,
        total=len(workspaces),
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace details",
    description="Get details of a specific workspace.",
    responses={
        200: {"description": "Workspace retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def get_workspace(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Get workspace details."""
    workspace = service.get_workspace(workspace_id, user_id)
    return service.get_workspace_response(workspace, user_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
    description="Update workspace details. Only owners and admins can update.",
    responses={
        200: {"description": "Workspace updated successfully"},
        400: {"description": "Validation error or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Update workspace details."""
    workspace = service.update_workspace(workspace_id, user_id, data)
    return service.get_workspace_response(workspace, user_id)


@router.post(
    "/{workspace_id}:archive",
    response_model=WorkspaceResponse,
    summary="Archive workspace",
    description="Archive a workspace. Only the owner can archive.",
    responses={
        200: {"description": "Workspace archived successfully"},
        400: {"description": "Workspace already archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def archive_workspace(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Archive a workspace."""
    workspace = service.archive_workspace(workspace_id, user_id)
    return service.get_workspace_response(workspace, user_id)


@router.post(
    "/{workspace_id}:unarchive",
    response_model=WorkspaceResponse,
    summary="Unarchive workspace",
    description="Unarchive a workspace. Only the owner can unarchive.",
    responses={
        200: {"description": "Workspace unarchived successfully"},
        400: {"description": "Workspace not archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def unarchive_workspace(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Unarchive a workspace."""
    workspace = service.unarchive_workspace(workspace_id, user_id)
    return service.get_workspace_response(workspace, user_id)


@router.post(
    "/{workspace_id}:leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave workspace",
    description="Leave a workspace. Owners cannot leave without transferring ownership.",
    responses={
        204: {"description": "Successfully left workspace"},
        400: {"description": "Owner cannot leave or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace not found"},
    },
)
def leave_workspace(
    workspace_id: UUID,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """Leave a workspace."""
    service.leave_workspace(workspace_id, user_id)


@router.post(
    "/{workspace_id}/owner:transfer",
    response_model=WorkspaceResponse,
    summary="Transfer ownership",
    description="Transfer workspace ownership to another member. Only the current owner can transfer.",
    responses={
        200: {"description": "Ownership transferred successfully"},
        400: {"description": "Validation error or workspace archived"},
        401: {"description": "Unauthorized"},
        403: {"description": "Access denied"},
        404: {"description": "Workspace or member not found"},
    },
)
def transfer_ownership(
    workspace_id: UUID,
    new_owner_id: int,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Transfer workspace ownership to another member."""
    workspace = service.transfer_ownership(workspace_id, new_owner_id, user_id)
    return service.get_workspace_response(workspace, user_id)


@router.get(
    "/me/workspaces",
    response_model=WorkspaceListResponse,
    summary="Get my workspaces",
    description="Convenience endpoint to get all workspaces for the current user.",
    responses={
        200: {"description": "Workspaces retrieved successfully"},
        401: {"description": "Unauthorized"},
    },
)
def get_my_workspaces(
    include_archived: bool = False,
    user_id: int = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceListResponse:
    """Get all workspaces for the current user (convenience endpoint)."""
    workspaces = service.get_user_workspaces(user_id, include_archived)

    items = [service.get_workspace_response(w, user_id) for w in workspaces]

    ordered_ids = service._get_ordered_ids(user_id)
    read_only_ids = service.subscription_client.get_read_only_ids(user_id, "workspaces", ordered_ids)
    for item in items:
        item.is_read_only = item.id in read_only_ids

    return WorkspaceListResponse(
        workspaces=items,
        total=len(workspaces),
    )

