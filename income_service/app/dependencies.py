from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.income import IncomeService
from app.clients.account_service_client import AccountServiceClient
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

def get_account_service_client() -> AccountServiceClient:
    """Get account service client instance"""
    return AccountServiceClient()

def get_income_service(db: Session = Depends(get_db), account_client: AccountServiceClient = Depends(get_account_service_client)) -> IncomeService:
    """Get income service instance"""
    return IncomeService(db, account_client)

def get_income_service_internal(
    db: Session = Depends(get_db),
    account_client: AccountServiceClient = Depends(get_account_service_client)
) -> IncomeService:
    """Get income service for internal use without user authentication"""
    return IncomeService(db, account_client)
