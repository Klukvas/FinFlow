"""
Shared WorkspaceAuthorizationMixin.

Replaces 7 per-service app/services/workspace_authorization.py files.

Each service passes its own exception factories so domain-specific exceptions
are still raised (e.g. AccountOwnershipError, IncomeValidationError).

Usage:
    class ExpenseService(WorkspaceAuthorizationMixin):
        def __init__(self, db):
            super().__init__(
                access_denied_error=lambda msg: ExpenseValidationError(msg, ErrorCode.VALIDATION_FAILED),
                workspace_mismatch_error=lambda msg: ExpenseValidationError(msg, ErrorCode.VALIDATION_FAILED),
            )
"""

from typing import Callable, Optional
from uuid import UUID

from shared.clients.workspace import WorkspaceClient
from shared.logging import get_logger

logger = get_logger(__name__)


class WorkspaceAuthorizationMixin:
    """Mixin to add workspace authorization to services."""

    def __init__(
        self,
        access_denied_error: Callable[[str], Exception],
        workspace_mismatch_error: Callable[[str], Exception],
    ):
        self.workspace_client = WorkspaceClient()
        self._access_denied_error = access_denied_error
        self._workspace_mismatch_error = workspace_mismatch_error

    def authorize_workspace_access(
        self,
        workspace_id: UUID,
        user_id: int,
        required_role: str = "viewer",
        operation: str = "access",
    ) -> str:
        """
        Authorize user access to workspace.

        Returns user's role in workspace.
        Raises the configured access_denied_error if unauthorized.
        """
        authorized, role = self.workspace_client.authorize(
            workspace_id, user_id, required_role
        )

        if not authorized or not role:
            logger.warning(
                f"User {user_id} not authorized for {operation} in workspace {workspace_id}",
                category="security",
                operation="workspace_authorization_failed",
                user_id=user_id,
                workspace_id=str(workspace_id),
                required_role=required_role,
                operation_type=operation,
            )
            raise self._access_denied_error(
                f"You do not have {required_role} access to this workspace"
            )

        logger.info(
            f"User {user_id} authorized for {operation} in workspace {workspace_id} with role {role}",
            category="security",
            operation="workspace_authorization_success",
            user_id=user_id,
            workspace_id=str(workspace_id),
            user_role=role,
            operation_type=operation,
        )

        return role

    def validate_workspace_match(
        self,
        entity_workspace_id: UUID,
        requested_workspace_id: UUID,
        entity_id: int,
        entity_name: str = "Resource",
    ) -> None:
        """
        Validate that entity belongs to the requested workspace.

        Raises the configured workspace_mismatch_error if they don't match.
        """
        if entity_workspace_id != requested_workspace_id:
            logger.warning(
                f"Workspace mismatch for {entity_name} {entity_id}",
                category="security",
                operation="workspace_mismatch",
                entity_id=entity_id,
                entity_workspace_id=str(entity_workspace_id),
                requested_workspace_id=str(requested_workspace_id),
            )
            raise self._workspace_mismatch_error(
                f"{entity_name} does not belong to the specified workspace"
            )
