from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.user import (
    UserCreate, UserLogin, UserOut, UserUpdate, 
    PasswordChange, TokenResponse, RefreshTokenRequest
)
from app.services.auth import AuthService
from app.dependencies import get_auth_service, get_current_user_id
from app.exceptions import (
    UserNotFoundError,
    UserValidationError,
    UserAuthenticationError,
    UserRegistrationError,
    PasswordPolicyError,
    UsernamePolicyError,
    AccountLockedError,
    RateLimitError,
    UserErrorCode
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register", 
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Validation error or user already exists"},
        429: {"description": "Rate limit exceeded"},
    }
)
def register(
    user: UserCreate, 
    service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Register a new user account.
    
    - **email**: User's email address (must be unique)
    - **username**: Unique username (3-50 characters, alphanumeric, underscores, hyphens)
    - **password**: Strong password (8-128 characters, must include uppercase, lowercase, numbers, and special characters)
    
    Returns an access token for immediate authentication.
    """
    try:
        db_user = service.create_user(user)
        token = service.create_token(db_user)
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except (UserRegistrationError, PasswordPolicyError, UsernamePolicyError, UserValidationError):
        raise
    except Exception as e:
        raise UserValidationError("Registration failed")

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user with email and password",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        423: {"description": "Account locked due to too many failed attempts"},
        429: {"description": "Rate limit exceeded"},
    }
)
def login(
    user: UserLogin, 
    service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Login with email and password.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns an access token for authentication.
    """
    try:
        db_user = service.authenticate_user(user)
        token = service.create_token(db_user)
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except (UserAuthenticationError, AccountLockedError, RateLimitError):
        raise
    except Exception as e:
        raise UserAuthenticationError("Login failed")

@router.get(
    "/me", 
    response_model=UserOut,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_me(
    user_id: int = Depends(get_current_user_id), 
    service: AuthService = Depends(get_auth_service)
) -> UserOut:
    """
    Get current user information.
    
    Returns the user's ID, email, and username for the authenticated user.
    """
    try:
        user = service.get_user_by_id(user_id)
        return user
    except UserNotFoundError:
        raise
    except Exception as e:
        raise UserValidationError("Failed to retrieve user information")

@router.put(
    "/me",
    response_model=UserOut,
    summary="Update current user",
    description="Update current user's email or username",
    responses={
        200: {"description": "User updated successfully"},
        400: {"description": "Validation error or username/email already exists"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def update_me(
    user_update: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
) -> UserOut:
    """
    Update current user information.
    
    - **email**: New email address (optional)
    - **username**: New username (optional)
    
    Only provided fields will be updated.
    """
    try:
        user = service.get_user_by_id(user_id)
        
        # Update email if provided
        if user_update.email is not None:
            # Check if email is already taken by another user
            existing_user = service.get_user_by_email(user_update.email)
            if existing_user and existing_user.id != user_id:
                error = UserValidationError("Email already registered")
                error.error_code = UserErrorCode.EMAIL_ALREADY_TAKEN
                raise error
            user.email = user_update.email.lower().strip()
        
        # Update username if provided
        if user_update.username is not None:
            # Check if username is already taken by another user
            existing_user = service.get_user_by_username(user_update.username)
            if existing_user and existing_user.id != user_id:
                error = UserValidationError("Username already taken")
                error.error_code = UserErrorCode.USERNAME_ALREADY_TAKEN
                raise error
            user.username = user_update.username.strip()
        
        if user_update.base_currency is not None:
            user.base_currency = user_update.base_currency.strip()
        
        service.db.commit()
        service.db.refresh(user)
        
        return user
    except (UserValidationError, UsernamePolicyError):
        service.db.rollback()
        raise
    except Exception as e:
        service.db.rollback()
        raise UserValidationError("Failed to update user information")

@router.post(
    "/change-password",
    summary="Change password",
    description="Change current user's password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Validation error or current password incorrect"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def change_password(
    password_change: PasswordChange,
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet security requirements)
    """
    try:
        service.change_password(
            user_id, 
            password_change.current_password, 
            password_change.new_password
        )
        return {"detail": "Password changed successfully"}
    except (UserAuthenticationError, PasswordPolicyError):
        raise
    except Exception as e:
        raise UserValidationError("Failed to change password")

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using refresh token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token"},
    }
)
def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns a new access token.
    """
    try:
        token = service.refresh_token(refresh_request.refresh_token)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except UserAuthenticationError:
        raise
    except Exception as e:
        raise UserAuthenticationError("Failed to refresh token")