from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from app.models.member import MemberRole, MemberStatus


class MemberResponse(BaseModel):
    """Schema for member response with user details"""
    id: int = Field(description="Member record ID")
    workspace_id: UUID = Field(description="Workspace ID")
    user_id: int = Field(description="User ID")
    role: MemberRole = Field(description="Member role: owner, full, or read")
    status: MemberStatus = Field(description="Member status")
    joined_at: datetime = Field(description="Join timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    # Optional user details (populated when needed)
    email: Optional[str] = Field(None, description="Member's email (if fetched)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "role": "owner",
                "status": "active",
                "joined_at": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None,
                "email": "owner@example.com"
            }
        }
    )


class MemberRoleUpdate(BaseModel):
    """Schema for updating member role (owner only)"""
    role: Literal["read", "full"] = Field(
        ...,
        description="New role for the member: 'read' (view only) or 'full' (view + edit)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "full"
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

