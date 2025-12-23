"""Workspace Authorization Mixin for Services"""
from uuid import UUID
from fastapi import HTTPException, status
from app.clients.workspace import WorkspaceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkspaceAuthorizationMixin:
    """Mixin to add workspace authorization to services"""
    
    def __init__(self):
        self.workspace_client = WorkspaceClient()
    
    def authorize_workspace_access(
        self, 
        workspace_id: UUID, 
        user_id: int, 
        required_role: str = "viewer",
        operation: str = "access"
    ) -> str:
        """Authorize user access to workspace"""
        authorized, role = self.workspace_client.authorize(workspace_id, user_id, required_role)
        
        if not authorized or not role:
            logger.warning(f"User {user_id} not authorized for {operation} in workspace {workspace_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have {required_role} access to this workspace"
            )
        
        logger.info(f"User {user_id} authorized for {operation} in workspace {workspace_id} with role {role}")
        return role


