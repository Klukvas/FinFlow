from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re

class UserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com", "john.doe@company.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters, must include letters and numbers)",
        examples=["mypass123", "hello2024"]
    )
    base_currency: str = Field(
        default="USD",
        description="User's base currency code",
        examples=["UAH", "USD", "EUR", "GBP"]
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "base_currency": "UAH"
            }
        }
    )

class UserLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User's password",
        examples=["SecurePass123!"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!"
            }
        }
    )

class UserOut(BaseModel):
    id: int = Field(description="Unique user identifier", examples=[1, 2, 3])
    email: EmailStr = Field(description="User's email address", examples=["user@example.com"])
    base_currency: str = Field(description="User's base currency code", examples=["UAH", "USD", "EUR"])
    default_workspace_id: Optional[UUID] = Field(
        None,
        description="User's default workspace ID"
    )
    tutorial_version: int = Field(
        default=0,
        description="Tutorial completion version (0 = not completed, >0 = completed version)"
    )
    role: str = Field(
        default="user",
        description="User role (user or admin)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "john.doe@example.com",
                "base_currency": "UAH",
                "default_workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "tutorial_version": 1,
                "role": "user"
            }
        }
    )

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    base_currency: Optional[str] = Field(
        None,
        description="New base currency code"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "new.email@example.com",
                "base_currency": "USD"
            }
        }
    )

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(
        ...,
        description="Current password"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters, must include letters and numbers)"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!"
            }
        }
    )

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(description="Refresh token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )

class TutorialUpdate(BaseModel):
    """Schema for updating tutorial completion status"""
    tutorial_version: int = Field(
        ...,
        ge=0,
        description="Tutorial version that user has completed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tutorial_version": 1
            }
        }
    )


# Admin-specific schemas
class AdminUserOut(BaseModel):
    """Full user details for admin view"""
    id: int
    email: EmailStr
    base_currency: str
    role: str
    status: str
    tutorial_version: int
    default_workspace_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """Paginated user list response for admin"""
    items: List[AdminUserOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class RoleUpdate(BaseModel):
    """Schema for updating user role"""
    role: str = Field(..., pattern="^(user|admin)$", description="User role")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"role": "admin"}
        }
    )


class StatusUpdate(BaseModel):
    """Schema for updating user status"""
    status: str = Field(..., pattern="^(active|disabled)$", description="User status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "disabled"}
        }
    )
