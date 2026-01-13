from sqlalchemy.orm import Session
from fastapi import Depends, Request, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.utils.logger import get_logger, log_security_event

logger = get_logger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

def get_database_session() -> Session:
    """Get database session dependency"""
    return Depends(get_db)

def verify_internal_token(request: Request) -> None:
    """Verify internal service token for inter-service communication"""
    token = request.headers.get("X-Internal-Token")
    if not token:
        log_security_event(logger, "Missing internal token", details="X-Internal-Token header not provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal token required"
        )
    
    if token != settings.INTERNAL_SECRET_TOKEN:
        log_security_event(logger, "Invalid internal token", details="Token mismatch")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access"
        )

def decode_token(token: str) -> int:
    """Decode JWT token and extract user ID"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
        return user_id
    except (JWTError, KeyError, ValueError) as e:
        logger.warning(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Extract and validate user ID from Bearer token"""
    if not credentials or not credentials.credentials:
        log_security_event(logger, "Missing authorization token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authorization token required"
        )
    
    return decode_token(credentials.credentials)

def get_workspace_id(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")
) -> UUID:
    """Extract and validate workspace ID from header"""
    if not x_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id header required"
        )
    try:
        return UUID(x_workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )
