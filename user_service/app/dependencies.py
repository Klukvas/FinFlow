from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.auth import AuthService
from app.utils.logger import get_logger, log_security_event
from typing import Generator

logger = get_logger(__name__)

# Constants
BEARER_PREFIX = "Bearer "

def get_db() -> Generator[Session, None, None]:
    """Database dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get auth service with database dependency"""
    return AuthService(db)

def get_current_user_id(request: Request, service: AuthService = Depends(get_auth_service)) -> int:
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
    
    try:
        return service.decode_token(token)
    except Exception as e:
        log_security_event(logger, "Token validation failed", details=f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )