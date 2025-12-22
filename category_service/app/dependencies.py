from fastapi import Depends, HTTPException, status, Request, Header
from app.services.category import CategoryService
from app.services.mcc_categories import DefaultCategoryService
from sqlalchemy.orm import Session
from app.database import SessionLocal
from typing import Generator, Optional
from jose import JWTError, jwt
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from uuid import UUID

logger = get_logger(__name__)

# Constants
INTERNAL_USER_ID_PLACEHOLDER = 0  # Placeholder for internal service calls
BEARER_PREFIX = "Bearer "

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

def get_current_user_id(request: Request) -> int:
    """Extract and validate user ID from Authorization header"""
    logger.debug(
        "[AUTH] Extracting user ID from token",
        category="auth",
        operation="extract_user_id",
        path=str(request.url.path),
        method=request.method
    )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        log_security_event(logger, "Missing authorization header")
        logger.error(
            "[AUTH] Missing Authorization header",
            category="auth",
            operation="auth_missing_header",
            path=str(request.url.path),
            method=request.method,
            headers_present=list(request.headers.keys())
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authorization header required"
        )
    
    if not auth_header.startswith(BEARER_PREFIX):
        log_security_event(logger, "Invalid authorization format", details=f"Expected Bearer token, got: {auth_header[:10]}...")
        logger.error(
            "[AUTH] Invalid Authorization format",
            category="auth",
            operation="auth_invalid_format",
            path=str(request.url.path),
            method=request.method,
            auth_header_prefix=auth_header[:20]
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token format. Expected 'Bearer <token>'"
        )

    token = auth_header[len(BEARER_PREFIX):].strip()
    if not token:
        log_security_event(logger, "Empty token in authorization header")
        logger.error(
            "[AUTH] Empty token",
            category="auth",
            operation="auth_empty_token",
            path=str(request.url.path),
            method=request.method
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token cannot be empty"
        )
    
    user_id = decode_token(token)
    logger.debug(
        f"[AUTH] Successfully extracted user_id: {user_id}",
        category="auth",
        operation="auth_success",
        user_id=user_id,
        path=str(request.url.path),
        method=request.method
    )
    
    return user_id


def get_workspace_id(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")) -> UUID:
    """Extract and validate workspace ID from X-Workspace-Id header"""
    logger.debug(
        "[WORKSPACE] Extracting workspace ID from header",
        category="workspace",
        operation="extract_workspace_id",
        workspace_id_raw=x_workspace_id
    )
    
    if not x_workspace_id:
        log_security_event(logger, "Missing workspace ID header")
        logger.error(
            "[WORKSPACE] Missing X-Workspace-Id header",
            category="workspace",
            operation="workspace_missing_header"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id header is required"
        )
    
    try:
        workspace_id = UUID(x_workspace_id)
        logger.debug(
            f"[WORKSPACE] Successfully parsed workspace_id: {workspace_id}",
            category="workspace",
            operation="workspace_parse_success",
            workspace_id=str(workspace_id)
        )
        return workspace_id
    except ValueError as e:
        log_security_event(logger, "Invalid workspace ID format", details=f"Invalid UUID: {x_workspace_id}")
        logger.error(
            "[WORKSPACE] Invalid workspace ID format",
            category="workspace",
            operation="workspace_invalid_format",
            workspace_id_raw=x_workspace_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )

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

def get_category_service(
    db: Session = Depends(get_db)
) -> CategoryService:
    """Get category service with user authentication"""
    return CategoryService(db)

def get_default_category_service(
    db: Session = Depends(get_db)
) -> DefaultCategoryService:
    """Get default category service"""
    return DefaultCategoryService(db)

def get_category_service_internal(
    db: Session = Depends(get_db)
) -> CategoryService:
    """Get category service for internal service calls"""
    return CategoryService(db)

