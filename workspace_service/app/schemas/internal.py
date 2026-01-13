from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
from uuid import UUID
from app.models.member import MemberRole


# Mapping old role names to new ones for backward compatibility
ROLE_MIGRATION_MAP = {
    "member": "read",
    "viewer": "read",
    "admin": "full",
}


class AuthorizeRequest(BaseModel):
    """Schema for authorization request from domain services"""
    user_id: int = Field(description="User ID to authorize")
    required_role: MemberRole = Field(
        default=MemberRole.READ,
        description="Minimum required role (read, full, or owner)"
    )

    @field_validator("required_role", mode="before")
    @classmethod
    def migrate_old_role_names(cls, v):
        """Convert old role names to new ones for backward compatibility"""
        if isinstance(v, str):
            v = ROLE_MIGRATION_MAP.get(v.lower(), v)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "required_role": "read"
            }
        }
    )


class AuthorizeResponse(BaseModel):
    """Schema for authorization response"""
    authorized: bool = Field(description="Whether user is authorized")
    role: Optional[MemberRole] = Field(None, description="User's role in the workspace")
    workspace_id: UUID = Field(description="Workspace ID")
    user_id: int = Field(description="User ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "authorized": True,
                "role": "full",
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1
            }
        }
    )


class UserWorkspaceItem(BaseModel):
    """Schema for a workspace item in user workspaces list"""
    id: UUID = Field(description="Workspace ID")
    name: str = Field(description="Workspace name")
    role: MemberRole = Field(description="User's role in this workspace")
    type: str = Field(description="Workspace type")
    is_default: bool = Field(default=False, description="Whether this is user's default workspace")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Personal",
                "role": "owner",
                "type": "personal",
                "is_default": True
            }
        }
    )


class UserWorkspacesResponse(BaseModel):
    """Schema for user workspaces list response"""
    workspaces: List[UserWorkspaceItem] = Field(description="List of user's workspaces")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspaces": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Personal",
                        "role": "owner",
                        "type": "personal",
                        "is_default": True
                    }
                ]
            }
        }
    )


class CreatePersonalWorkspaceRequest(BaseModel):
    """Schema for creating a personal workspace during user registration"""
    user_id: int = Field(description="User ID for the new personal workspace")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1
            }
        }
    )


class CreatePersonalWorkspaceResponse(BaseModel):
    """Schema for personal workspace creation response"""
    workspace_id: UUID = Field(description="Created workspace ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class DefaultWorkspaceResponse(BaseModel):
    """Schema for default workspace response"""
    workspace_id: UUID = Field(description="Default workspace ID")
    name: str = Field(description="Workspace name")
    type: str = Field(description="Workspace type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Personal",
                "type": "personal"
            }
        }
    )

