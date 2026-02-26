from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.expense import ExpenseService
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.utils.logger import get_logger
from typing import Generator
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

logger = get_logger(__name__)

def get_category_service_client() -> CategoryServiceClient:
    """Get category service client instance"""
    return CategoryServiceClient()

def get_account_service_client() -> AccountServiceClient:
    """Get account service client instance"""
    return AccountServiceClient()

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
