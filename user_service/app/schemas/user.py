from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional
import re

class UserCreate(BaseModel):
    email: EmailStr = Field(
        ..., 
        description="User's email address",
        examples=["user@example.com", "john.doe@company.com"]
    )
    username: str = Field(
        ..., 
        min_length=3,
        max_length=50,
        description="Unique username (3-50 characters, alphanumeric, underscores, hyphens)",
        examples=["john_doe", "user123", "my-username"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters, must include uppercase, lowercase, numbers, and special characters)",
        examples=["SecurePass123!", "MyPassword2024#"]
    )
    base_currency: str = Field(
        default="USD",
        description="User's base currency code",
        examples=["UAH", "USD", "EUR", "GBP"]
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        if not re.match(r'^[a-zA-Z0-9]', v):
            raise ValueError('Username must start with a letter or number')
        if v.endswith('_') or v.endswith('-'):
            raise ValueError('Username cannot end with underscore or hyphen')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "username": "john_doe",
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
    username: str = Field(description="User's username", examples=["john_doe"])
    base_currency: str = Field(description="User's base currency code", examples=["UAH", "USD", "EUR"])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "john.doe@example.com",
                "username": "john_doe",
                "base_currency": "UAH"
            }
        }
    )

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="New username"
    )
    base_currency: Optional[str] = Field(
        None,
        description="New base currency code"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            if not re.match(r'^[a-zA-Z0-9]', v):
                raise ValueError('Username must start with a letter or number')
            if v.endswith('_') or v.endswith('-'):
                raise ValueError('Username cannot end with underscore or hyphen')
            return v.strip()
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "new.email@example.com",
                "username": "new_username",
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
        description="New password (8-128 characters, must include uppercase, lowercase, numbers, and special characters)"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
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
