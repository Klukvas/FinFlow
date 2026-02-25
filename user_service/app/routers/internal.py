import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from app.services.auth import AuthService
from app.dependencies import get_auth_service
from app.exceptions import UserNotFoundError
from app.schemas.user import UserOut
from typing import Optional
from app.config import settings

router = APIRouter(prefix="/internal", tags=["internal"])


def verify_internal_token(internal_token: Optional[str] = Header(None, alias="X-Internal-Token")) -> None:
    """Verify internal service token for inter-service communication"""
    if not internal_token or not secrets.compare_digest(internal_token, settings.INTERNAL_SECRET_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access"
        )


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user_internal(
    user_id: int,
    service: AuthService = Depends(get_auth_service),
    _: None = Depends(verify_internal_token)
) -> UserOut:
    """
    Internal endpoint to get user information by ID.
    Used by other services to fetch user details.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        User information including base_currency
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = service.get_user_by_id(user_id)
        return user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )


@router.get("/users/by-email/{email}", response_model=UserOut)
async def get_user_by_email_internal(
    email: str,
    service: AuthService = Depends(get_auth_service),
    _: None = Depends(verify_internal_token)
) -> UserOut:
    """
    Internal endpoint to get user information by email.
    Used by workspace service for invite creation.
    
    Args:
        email: The email address of the user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    user = service.get_user_by_email(email.lower().strip())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    return user

