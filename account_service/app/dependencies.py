from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.account import AccountService
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from shared.clients import CurrencyServiceClient
from app.utils.logger import get_logger
from typing import Generator
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

logger = get_logger(__name__)

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
    """Get currency service client singleton"""
    return CurrencyServiceClient.get_instance()

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
