from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.workspace import WorkspaceService
from app.services.invite import InviteService
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token


def get_workspace_service(db: Session = Depends(get_db)) -> WorkspaceService:
    """Get workspace service instance"""
    return WorkspaceService(db)


def get_invite_service(db: Session = Depends(get_db)) -> InviteService:
    """Get invite service instance"""
    return InviteService(db)
