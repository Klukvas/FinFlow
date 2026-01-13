"""Workspace Service Client for authorization"""
import httpx
from typing import Optional
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
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has required role in workspace.
        
        Args:
            workspace_id: The workspace ID to check
            user_id: The user ID to authorize
            required_role: Required role (viewer, member, admin, owner)
            
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
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
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
                    try:
                        response_body = response.text
                    except:
                        response_body = "unable to read"
                    
                    logger.error(
                        f"Unexpected response from workspace_service: {response.status_code}",
                        extra={
                            "operation": "workspace_authorize",
                            "user_id": user_id,
                            "workspace_id": str(workspace_id),
                            "status_code": response.status_code,
                            "response_body": response_body[:500],
                            "headers": dict(response.headers)
                        }
                    )
                    return False, None
                    
        except httpx.TimeoutException as e:
            import traceback
            logger.error(
                f"Timeout while authorizing user in workspace: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": "TimeoutException",
                    "traceback": traceback.format_exc()
                }
            )
            return False, None
        except httpx.RequestError as e:
            import traceback
            logger.error(
                f"Request error while authorizing user: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            return False, None
        except Exception as e:
            import traceback
            logger.error(
                f"Unexpected error while authorizing user: {e.__class__.__name__} - {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            return False, None

    def get_user_role(self, workspace_id: UUID, user_id: int) -> Optional[str]:
        """
        Get user's role in workspace.
        
        Args:
            workspace_id: The workspace ID
            user_id: The user ID
            
        Returns:
            User's role or None if not a member
        """
        try:
            url = f"{self.base_url}/internal/workspaces/{workspace_id}/role/{user_id}"
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("role")
                else:
                    return None
                    
        except Exception as e:
            logger.error(
                f"Error getting user role: {e}",
                extra={
                    "operation": "get_user_role",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id)
                }
            )
            return None


