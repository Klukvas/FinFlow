from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.income import IncomeService
from app.clients.user_service_client import UserServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.config import settings
from typing import Optional
from uuid import UUID
import jwt as pyjwt

# Security scheme for Swagger UI
security = HTTPBearer()

def get_account_service_client() -> AccountServiceClient:
    """Get account service client instance"""
    return AccountServiceClient()

def get_income_service(db: Session = Depends(get_db), account_client: AccountServiceClient = Depends(get_account_service_client)) -> IncomeService:
    """Get income service instance"""
    return IncomeService(db, account_client)

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Extract user ID from JWT token"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    try:
        token = credentials.credentials
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return int(user_id)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

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
