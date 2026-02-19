from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from typing import Optional
import math

from app.dependencies import get_current_admin_user, get_db
from app.models.user import User
from app.schemas.user import (
    AdminUserOut, 
    AdminUserListResponse, 
    RoleUpdate, 
    StatusUpdate
)
from app.utils.logger import get_logger, log_operation

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    search: Optional[str] = Query(None, description="Search by email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and search.
    Admin-only endpoint.
    """
    query = db.query(User)
    
    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            User.email.ilike(search_term)
        )
    
    # Get total count
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.order_by(User.id.desc()).offset(offset).limit(page_size).all()
    
    log_operation(
        logger,
        "Admin listed users",
        admin.id,
        f"Search: {search}, Page: {page}, Results: {len(users)}"
    )
    
    return AdminUserListResponse(
        items=[AdminUserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}", response_model=AdminUserOut)
def get_user(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID.
    Admin-only endpoint.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AdminUserOut.model_validate(user)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user role.
    Admin-only endpoint.
    Cannot remove your own admin role.
    """
    # Prevent admin from removing their own admin role
    if user_id == admin.id and role_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_role = user.role
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    log_operation(
        logger,
        "Admin updated user role",
        admin.id,
        f"User {user_id}: {old_role} -> {role_data.role}"
    )
    
    return AdminUserOut.model_validate(user)


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
def update_user_status(
    user_id: int,
    status_data: StatusUpdate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Enable/disable user account.
    Admin-only endpoint.
    Cannot disable your own account.
    """
    # Prevent admin from disabling themselves
    if user_id == admin.id and status_data.status == "disabled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_status = user.status
    user.status = status_data.status
    db.commit()
    db.refresh(user)
    
    log_operation(
        logger,
        "Admin updated user status",
        admin.id,
        f"User {user_id}: {old_status} -> {status_data.status}"
    )
    
    return AdminUserOut.model_validate(user)
