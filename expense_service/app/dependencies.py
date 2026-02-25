import secrets

from fastapi import Depends, Request, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.expense import ExpenseService
from jose import JWTError, jwt
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Generator, Optional
from uuid import UUID

logger = get_logger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

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

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Extract and validate user ID from Bearer token"""
    if not credentials or not credentials.credentials:
        log_security_event(logger, "Missing authorization token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authorization token required"
        )
    
    return decode_token(credentials.credentials)

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

def verify_internal_token(request: Request) -> None:
    """Verify internal service token for inter-service communication"""
    token = request.headers.get("X-Internal-Token")
    if not token or not secrets.compare_digest(token, settings.INTERNAL_SECRET_TOKEN):
        log_security_event(logger, "Invalid or missing internal token", details="Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access"
        )