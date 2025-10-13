from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.expense import ExpenseService
from jose import JWTError, jwt
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Generator

logger = get_logger(__name__)

# Constants
BEARER_PREFIX = "Bearer "

def get_category_service_client() -> CategoryServiceClient:
    """Get category service client instance"""
    return CategoryServiceClient()

def get_account_service_client() -> AccountServiceClient:
    """Get account service client instance"""
    return AccountServiceClient()

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

def get_expense_service(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    category_client: CategoryServiceClient = Depends(get_category_service_client),
    account_client: AccountServiceClient = Depends(get_account_service_client)
) -> ExpenseService:
    """Get expense service with all dependencies"""
    return ExpenseService(db, category_client, account_client)

def get_expense_service_internal(
    db: Session = Depends(get_db),
    category_client: CategoryServiceClient = Depends(get_category_service_client),
    account_client: AccountServiceClient = Depends(get_account_service_client)
) -> ExpenseService:
    """Get expense service for internal use without user authentication"""
    return ExpenseService(db, category_client, account_client)

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