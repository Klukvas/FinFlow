from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.account import AccountService
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from app.clients.currency_service_client import CurrencyServiceClient
from jose import JWTError, jwt
from app.config import settings
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
