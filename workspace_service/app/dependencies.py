from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.database import get_db
from app.config import settings
from app.services.workspace import WorkspaceService
from app.services.invite import InviteService
from app.utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)
security = HTTPBearer()


def get_workspace_service(db: Session = Depends(get_db)) -> WorkspaceService:
    """Get workspace service instance"""
    return WorkspaceService(db)


def get_invite_service(db: Session = Depends(get_db)) -> InviteService:
    """Get invite service instance with workspace service dependency"""
    workspace_service = WorkspaceService(db)
    return InviteService(db, workspace_service)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Extract user ID from JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return int(user_id)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_internal_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> None:
    """Verify internal service token for inter-service communication"""
    if credentials.credentials != settings.INTERNAL_SECRET_TOKEN:
        logger.warning("Invalid internal token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token"
        )

