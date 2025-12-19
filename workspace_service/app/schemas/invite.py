from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.invite import InviteStatus
from app.models.member import MemberRole


class InviteCreate(BaseModel):
    """Schema for creating a new invite"""
    invitee_user_id: Optional[int] = Field(
        None,
        description="User ID to invite (for direct invites)"
    )
    invitee_email: Optional[EmailStr] = Field(
        None,
        description="Email address to invite"
    )
    role: MemberRole = Field(
        default=MemberRole.MEMBER,
        description="Role to assign to the invitee"
    )

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: MemberRole) -> MemberRole:
        """Cannot invite someone as owner"""
        if v == MemberRole.OWNER:
            raise ValueError("Cannot invite someone as owner. Use ownership transfer instead.")
        return v

    def model_post_init(self, __context):
        """Ensure at least one of invitee_user_id or invitee_email is provided"""
        if not self.invitee_user_id and not self.invitee_email:
            raise ValueError("Either invitee_user_id or invitee_email must be provided")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invitee_email": "john@example.com",
                "role": "member"
            }
        }
    )


class InviteResponse(BaseModel):
    """Schema for invite response"""
    id: UUID = Field(description="Invite ID")
    workspace_id: UUID = Field(description="Workspace ID")
    inviter_user_id: int = Field(description="Inviter user ID")
    invitee_user_id: Optional[int] = Field(None, description="Invitee user ID")
    invitee_email: Optional[str] = Field(None, description="Invitee email")
    status: InviteStatus = Field(description="Invite status")
    expires_at: datetime = Field(description="Expiration timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    invite_token: Optional[str] = Field(None, description="Invite token (only returned on creation)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "550e8400-e29b-41d4-a716-446655440001",
                "inviter_user_id": 1,
                "invitee_email": "john@example.com",
                "status": "pending",
                "expires_at": "2024-01-08T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "accepted_at": None
            }
        }
    )


class InviteListResponse(BaseModel):
    """Schema for list of invites response"""
    invites: List[InviteResponse] = Field(description="List of invites")
    total: int = Field(description="Total number of invites")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invites": [],
                "total": 0
            }
        }
    )


class InviteAcceptRequest(BaseModel):
    """Schema for accepting an invite"""
    # Token is passed in the URL path, this is for any additional data if needed
    pass

    model_config = ConfigDict(
        json_schema_extra={
            "example": {}
        }
    )

