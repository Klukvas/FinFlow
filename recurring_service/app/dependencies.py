from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

def get_database_session() -> Session:
    """Get database session dependency"""
    return Depends(get_db)
