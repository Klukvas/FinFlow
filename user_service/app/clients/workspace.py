"""Workspace Service Client for internal communication"""
import httpx
from typing import Optional
from uuid import UUID
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class WorkspaceClient:
    """Client for communicating with workspace_service internal API"""

    def __init__(self):
        self.base_url = settings.WORKSPACE_SERVICE_URL
        self.internal_token = settings.INTERNAL_SECRET_TOKEN
        self.timeout = 10.0

    def _get_headers(self) -> dict:
        """Get headers for internal API calls"""
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def create_personal_workspace(self, user_id: int) -> Optional[UUID]:
        """
        Create a personal workspace for a new user.
        
        Args:
            user_id: The ID of the user to create workspace for
            
        Returns:
            UUID of the created workspace, or None if creation failed
        """
        try:
            url = f"{self.base_url}/internal/workspaces/personal"
            payload = {"user_id": user_id}
            
            logger.info(
                "Creating personal workspace",
                extra={
                    "operation": "workspace_create",
                    "user_id": user_id,
                    "url": url
                }
            )
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                
                if response.status_code == 201:
                    data = response.json()
                    workspace_id = UUID(data["workspace_id"])
                    logger.info(
                        "Personal workspace created successfully",
                        extra={
                            "operation": "workspace_create",
                            "user_id": user_id,
                            "workspace_id": str(workspace_id)
                        }
                    )
                    return workspace_id
                else:
                    logger.warning(
                        f"Failed to create personal workspace: {response.status_code} - {response.text}",
                        extra={
                            "operation": "workspace_create",
                            "user_id": user_id,
                            "status_code": response.status_code
                        }
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(
                "Timeout while creating personal workspace",
                extra={"operation": "workspace_create", "user_id": user_id}
            )
            return None
        except httpx.RequestError as e:
            logger.warning(
                f"Request error while creating personal workspace: {e}",
                extra={"operation": "workspace_create", "user_id": user_id}
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while creating personal workspace: {e}",
                extra={"operation": "workspace_create", "user_id": user_id}
            )
            return None

    def get_user_default_workspace(self, user_id: int) -> Optional[UUID]:
        """
        Get user's default (personal) workspace ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            UUID of the default workspace, or None if not found
        """
        try:
            url = f"{self.base_url}/internal/users/{user_id}/default-workspace"
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    workspace_id = UUID(data["workspace_id"])
                    logger.info(
                        "Retrieved default workspace",
                        extra={
                            "operation": "workspace_get_default",
                            "user_id": user_id,
                            "workspace_id": str(workspace_id)
                        }
                    )
                    return workspace_id
                elif response.status_code == 404:
                    logger.info(
                        "No default workspace found for user",
                        extra={
                            "operation": "workspace_get_default",
                            "user_id": user_id
                        }
                    )
                    return None
                else:
                    logger.warning(
                        f"Failed to get default workspace: {response.status_code} - {response.text}",
                        extra={
                            "operation": "workspace_get_default",
                            "user_id": user_id,
                            "status_code": response.status_code
                        }
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(
                "Timeout while getting default workspace",
                extra={"operation": "workspace_get_default", "user_id": user_id}
            )
            return None
        except httpx.RequestError as e:
            logger.warning(
                f"Request error while getting default workspace: {e}",
                extra={"operation": "workspace_get_default", "user_id": user_id}
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while getting default workspace: {e}",
                extra={"operation": "workspace_get_default", "user_id": user_id}
            )
            return None

