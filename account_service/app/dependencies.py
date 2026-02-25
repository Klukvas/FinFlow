import secrets

from fastapi import Depends, Request, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.account import AccountService
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from app.clients.currency_service_client import CurrencyServiceClient
from jose import JWTError, jwt
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Generator, Optional
from uuid import UUID

logger = get_logger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

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

def get_expense_client() -> ExpenseServiceClient:
    """Get expense service client instance"""
    return ExpenseServiceClient()

def get_income_client() -> IncomeServiceClient:
    """Get income service client instance"""
    return IncomeServiceClient()

def get_currency_client() -> CurrencyServiceClient:
    """Get currency service client instance"""
    return CurrencyServiceClient()

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

def get_account_service(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    expense_client: ExpenseServiceClient = Depends(get_expense_client),
    income_client: IncomeServiceClient = Depends(get_income_client),
    currency_client: CurrencyServiceClient = Depends(get_currency_client)
) -> AccountService:
    """Get account service with all dependencies"""
    return AccountService(db, expense_client, income_client, currency_client)

def get_account_service_internal(
    db: Session = Depends(get_db),
    expense_client: ExpenseServiceClient = Depends(get_expense_client),
    income_client: IncomeServiceClient = Depends(get_income_client),
    currency_client: CurrencyServiceClient = Depends(get_currency_client)
) -> AccountService:
    """Get account service for internal use without user authentication"""
    return AccountService(db, expense_client, income_client, currency_client)

def verify_internal_token(request: Request) -> None:
    """Verify internal service token for inter-service communication"""
    token = request.headers.get("X-Internal-Token")
    if not token or not secrets.compare_digest(token, settings.INTERNAL_SECRET_TOKEN):
        log_security_event(logger, "Invalid or missing internal token", details="Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access"
        )
