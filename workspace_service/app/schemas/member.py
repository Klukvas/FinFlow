from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.member import MemberRole, MemberStatus


class MemberResponse(BaseModel):
    """Schema for member response"""
    id: int = Field(description="Member record ID")
    workspace_id: UUID = Field(description="Workspace ID")
    user_id: int = Field(description="User ID")
    role: MemberRole = Field(description="Member role")
    status: MemberStatus = Field(description="Member status")
    joined_at: datetime = Field(description="Join timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "role": "member",
                "status": "active",
                "joined_at": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None
            }
        }
    )


class MemberRoleUpdate(BaseModel):
    """Schema for updating member role"""
    role: MemberRole = Field(
        ...,
        description="New role for the member"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "admin"
            }
        }
    )


class MemberListResponse(BaseModel):
    """Schema for list of members response"""
    members: List[MemberResponse] = Field(description="List of members")
    total: int = Field(description="Total number of members")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "members": [],
                "total": 0
            }
        }
    )

