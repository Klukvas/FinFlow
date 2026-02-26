from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.debt import DebtService
from app.services.contact import ContactService
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

def get_debt_service(db: Session = Depends(get_db)) -> DebtService:
    """Dependency to get debt service"""
    return DebtService(db)

def get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    """Dependency to get contact service"""
    return ContactService(db)
