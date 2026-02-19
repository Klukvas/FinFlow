from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, computed_field
from typing import Optional, List, Literal
from datetime import datetime, timezone
from uuid import UUID
from app.models.invite import InviteStatus
from app.models.member import MemberRole


def _get_utc_now():
    """Get current UTC time, timezone-aware"""
    return datetime.now(timezone.utc)


def _normalize_datetime(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC) for comparison"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class InviteCreate(BaseModel):
    """
    Schema for creating a new workspace invite.
    Owner invites by email - user must exist in the system.
    """
    email: EmailStr = Field(
        ...,
        description="Email of the user to invite (must be an existing user)"
    )
    role: Literal["read", "full"] = Field(
        default="read",
        description="Role to assign: 'read' (view only) or 'full' (view + edit)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "colleague@example.com",
                "role": "read"
            }
        }
    )


class InviteResponse(BaseModel):
    """Schema for invite response (owner view - when listing workspace invites)"""
    id: UUID = Field(description="Invite ID")
    workspace_id: UUID = Field(description="Workspace ID")
    inviter_user_id: int = Field(description="Inviter user ID")
    invitee_user_id: int = Field(description="Invitee user ID")
    invitee_email: str = Field(description="Invitee email")
    role: MemberRole = Field(description="Role to be assigned upon acceptance")
    status: InviteStatus = Field(description="Invite status")
    expires_at: datetime = Field(description="Expiration timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    responded_at: Optional[datetime] = Field(None, description="When invitee responded")

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if the invite has expired based on time"""
        # Normalize both datetimes to be timezone-aware for comparison
        expires = _normalize_datetime(self.expires_at)
        now = _get_utc_now()
        return expires <= now

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "550e8400-e29b-41d4-a716-446655440001",
                "inviter_user_id": 1,
                "invitee_user_id": 2,
                "invitee_email": "colleague@example.com",
                "role": "read",
                "status": "pending",
                "expires_at": "2024-01-08T00:00:00Z",
                "created_at": "2024-01-05T00:00:00Z",
                "responded_at": None,
                "is_expired": False
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


class MyInviteResponse(BaseModel):
    """
    Schema for incoming invite (invitee view).
    Includes rich data for frontend display.
    """
    id: UUID = Field(description="Invite ID")
    workspace_id: UUID = Field(description="Workspace ID")
    workspace_name: str = Field(description="Name of the workspace")
    inviter_user_id: int = Field(description="Inviter user ID")
    inviter_email: str = Field(description="Inviter's email")
    role: MemberRole = Field(description="Role that will be assigned upon acceptance")
    status: InviteStatus = Field(description="Invite status")
    expires_at: datetime = Field(description="Expiration timestamp")
    created_at: datetime = Field(description="Creation timestamp")

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if the invite has expired based on time"""
        # Normalize both datetimes to be timezone-aware for comparison
        expires = _normalize_datetime(self.expires_at)
        now = _get_utc_now()
        return expires <= now

    @computed_field
    @property
    def is_actionable(self) -> bool:
        """Check if the invite can be accepted/rejected"""
        return self.status == InviteStatus.PENDING and not self.is_expired

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "550e8400-e29b-41d4-a716-446655440001",
                "workspace_name": "Family Budget",
                "inviter_user_id": 1,
                "inviter_email": "owner@example.com",
                "role": "full",
                "status": "pending",
                "expires_at": "2024-01-08T00:00:00Z",
                "created_at": "2024-01-05T00:00:00Z",
                "is_expired": False,
                "is_actionable": True
            }
        }
    )


class MyInviteListResponse(BaseModel):
    """Schema for list of incoming invites (invitee view)"""
    invites: List[MyInviteResponse] = Field(description="List of incoming invites")
    total: int = Field(description="Total number of invites")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invites": [],
                "total": 0
            }
        }
    )

