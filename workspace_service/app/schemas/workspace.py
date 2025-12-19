from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.workspace import WorkspaceType


class WorkspaceCreate(BaseModel):
    """Schema for creating a new workspace"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Workspace name",
        examples=["My Shared Budget", "Family Finances"]
    )
    type: WorkspaceType = Field(
        default=WorkspaceType.SHARED,
        description="Workspace type (personal or shared)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Family Budget",
                "type": "shared"
            }
        }
    )


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New workspace name"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Workspace Name"
            }
        }
    )


class WorkspaceResponse(BaseModel):
    """Schema for workspace response"""
    id: UUID = Field(description="Unique workspace identifier")
    name: str = Field(description="Workspace name")
    type: WorkspaceType = Field(description="Workspace type")
    owner_user_id: int = Field(description="Owner user ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    is_archived: bool = Field(description="Whether workspace is archived")
    member_count: Optional[int] = Field(None, description="Number of active members")
    current_user_role: Optional[str] = Field(None, description="Current user's role in this workspace")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Family Budget",
                "type": "shared",
                "owner_user_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None,
                "archived_at": None,
                "is_archived": False,
                "member_count": 3,
                "current_user_role": "owner"
            }
        }
    )


class WorkspaceListResponse(BaseModel):
    """Schema for list of workspaces response"""
    workspaces: List[WorkspaceResponse] = Field(description="List of workspaces")
    total: int = Field(description="Total number of workspaces")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspaces": [],
                "total": 0
            }
        }
    )

