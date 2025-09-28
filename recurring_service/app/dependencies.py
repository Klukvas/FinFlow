from sqlalchemy.orm import Session
from fastapi import Depends, Request, HTTPException, status
from jose import JWTError, jwt
from app.config import settings

from app.database import get_db
from app.utils.logger import get_logger, log_security_event

logger = get_logger(__name__)

BEARER_PREFIX = "Bearer "

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
    
    if token != settings.INTERNAL_SECRET:
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

def get_current_user_id(request: Request) -> int:
    """Extract and validate user ID from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        log_security_event(logger, "Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authorization header required"
        )
    
    if not auth_header.startswith(BEARER_PREFIX):
        log_security_event(logger, "Invalid authorization format", details=f"Expected Bearer token, got: {auth_header[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token format. Expected 'Bearer <token>'"
        )

    token = auth_header[len(BEARER_PREFIX):].strip()
    if not token:
        log_security_event(logger, "Empty token in authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token cannot be empty"
        )
    
    return decode_token(token)
