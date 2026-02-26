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
    ) -> tuple[bool, Optional[str]]:
        """Check if user has required role in workspace"""
        try:
            url = f"{self.base_url}/internal/workspaces/{workspace_id}/authorize"
            payload = {"user_id": user_id, "required_role": required_role}

            response = self.client.post(url, json=payload, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                return data.get("authorized", False), data.get("role")
            else:
                return False, None

        except Exception as e:
            logger.error(f"Workspace authorization error: {e}")
            return False, None
