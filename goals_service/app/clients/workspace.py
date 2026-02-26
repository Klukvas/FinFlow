"""Workspace Service Client for authorization"""
import httpx
from typing import Optional, Tuple
from uuid import UUID
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkspaceClient:
    """Client for communicating with workspace_service for authorization"""

    def __init__(self):
        self.base_url = settings.WORKSPACE_SERVICE_URL
        self.internal_token = settings.INTERNAL_SECRET_TOKEN
        self.timeout = 5.0
        self.client = httpx.Client(timeout=self.timeout)

    def _get_headers(self) -> dict:
        """Get headers for internal API calls"""
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def authorize(
        self,
        workspace_id: UUID,
        user_id: int,
        required_role: str = "viewer"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has required role in workspace.

        Returns:
            Tuple of (authorized: bool, user_role: Optional[str])
        """
        try:
            url = f"{self.base_url}/internal/workspaces/{workspace_id}/authorize"
            payload = {
                "user_id": user_id,
                "required_role": required_role
            }

            logger.info(
                "Authorizing user in workspace",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "required_role": required_role
                }
            )

            response = self.client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                authorized = data.get("authorized", False)
                role = data.get("role")

                logger.info(
                    "Authorization check completed",
                    extra={
                        "operation": "workspace_authorize",
                        "user_id": user_id,
                        "workspace_id": str(workspace_id),
                        "authorized": authorized,
                        "role": role
                    }
                )
                return authorized, role
            elif response.status_code == 403:
                logger.warning(
                    "User not authorized in workspace",
                    extra={
                        "operation": "workspace_authorize",
                        "user_id": user_id,
                        "workspace_id": str(workspace_id),
                        "required_role": required_role
                    }
                )
                return False, None
            elif response.status_code == 404:
                logger.warning(
                    "Workspace not found",
                    extra={
                        "operation": "workspace_authorize",
                        "workspace_id": str(workspace_id)
                    }
                )
                return False, None
            else:
                logger.error(
                    f"Unexpected response from workspace_service: {response.status_code}",
                    extra={
                        "operation": "workspace_authorize",
                        "user_id": user_id,
                        "workspace_id": str(workspace_id),
                        "status_code": response.status_code
                    }
                )
                return False, None

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout while authorizing user in workspace: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id)
                }
            )
            return False, None
        except httpx.RequestError as e:
            logger.error(
                f"Request error while authorizing user: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id)
                }
            )
            return False, None
        except Exception as e:
            logger.error(
                f"Unexpected error while authorizing user: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id)
                }
            )
            return False, None

    def get_user_default_workspace(self, user_id: int) -> Optional[UUID]:
        """Get user's default (personal) workspace ID"""
        try:
            url = f"{self.base_url}/internal/users/{user_id}/default-workspace"

            response = self.client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                workspace_id = data.get("workspace_id")
                if workspace_id:
                    return UUID(workspace_id)
            return None

        except Exception as e:
            logger.error(f"Error getting default workspace for user {user_id}: {e}")
            return None
