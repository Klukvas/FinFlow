"""Workspace Authorization Mixin for Services"""
from uuid import UUID
from app.clients.workspace import WorkspaceClient
from app.exceptions import AccountOwnershipError
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
        """
        Authorize user access to workspace.
        
        Args:
            workspace_id: Workspace ID to check
            user_id: User ID to authorize
            required_role: Minimum required role
            operation: Operation name for logging
            
        Returns:
            User's role in workspace
            
        Raises:
            AccountOwnershipError: If user is not authorized
        """
        authorized, role = self.workspace_client.authorize(
            workspace_id, 
            user_id, 
            required_role
        )
        
        if not authorized or not role:
            logger.warning(
                f"User {user_id} not authorized for {operation} in workspace {workspace_id}",
                category="security",
                operation="workspace_authorization_failed",
                user_id=user_id,
                workspace_id=str(workspace_id),
                required_role=required_role,
                operation_type=operation
            )
            raise AccountOwnershipError(
                f"You do not have {required_role} access to this workspace"
            )
        
        logger.info(
            f"User {user_id} authorized for {operation} in workspace {workspace_id} with role {role}",
            category="security",
            operation="workspace_authorization_success",
            user_id=user_id,
            workspace_id=str(workspace_id),
            user_role=role,
            operation_type=operation
        )
        
        return role
    
    def validate_workspace_match(
        self,
        account_workspace_id: UUID,
        requested_workspace_id: UUID,
        account_id: int
    ) -> None:
        """
        Validate that account belongs to the requested workspace.
        
        Args:
            account_workspace_id: Workspace ID from account
            requested_workspace_id: Workspace ID from request
            account_id: Account ID for error message
            
        Raises:
            AccountOwnershipError: If workspaces don't match
        """
        if account_workspace_id != requested_workspace_id:
            logger.warning(
                f"Workspace mismatch for account {account_id}",
                category="security",
                operation="workspace_mismatch",
                account_id=account_id,
                account_workspace_id=str(account_workspace_id),
                requested_workspace_id=str(requested_workspace_id)
            )
            raise AccountOwnershipError(
                "Account does not belong to the specified workspace"
            )


