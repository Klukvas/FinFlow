from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.income import IncomeService
from app.clients.user_service_client import UserServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.config import settings
import jwt as pyjwt

def get_account_service_client() -> AccountServiceClient:
    """Get account service client instance"""
    return AccountServiceClient()

def get_income_service(db: Session = Depends(get_db), account_client: AccountServiceClient = Depends(get_account_service_client)) -> IncomeService:
    """Get income service instance"""
    return IncomeService(db, account_client)

def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    try:
        token = authorization.split(" ")[1]
        payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
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
