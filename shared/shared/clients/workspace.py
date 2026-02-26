"""
Unified WorkspaceClient for workspace authorization.

Replaces 8 identical per-service app/clients/workspace.py files.
"""

import os
import traceback
from typing import Optional
from uuid import UUID

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)


class WorkspaceClient:
    """Client for communicating with workspace_service for authorization."""

    def __init__(self):
        self.base_url = os.environ.get("WORKSPACE_SERVICE_URL", "http://workspace_service:8000")
        self.internal_token = os.environ.get("INTERNAL_SECRET_TOKEN", "")
        self.timeout = 5.0
        self.client = httpx.Client(timeout=self.timeout)

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def authorize(
        self,
        workspace_id: UUID,
        user_id: int,
        required_role: str = "viewer",
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has required role in workspace.

        Returns:
            Tuple of (authorized: bool, user_role: Optional[str])
        """
        try:
            url = f"{self.base_url}/internal/workspaces/{workspace_id}/authorize"
            payload = {
                "user_id": user_id,
                "required_role": required_role,
            }

            logger.info(
                "Authorizing user in workspace",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "required_role": required_role,
                },
            )

            response = self.client.post(
                url,
                json=payload,
                headers=self._get_headers(),
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
                        "role": role,
                    },
                )
                return authorized, role
            elif response.status_code == 403:
                logger.warning(
                    "User not authorized in workspace",
                    extra={
                        "operation": "workspace_authorize",
                        "user_id": user_id,
                        "workspace_id": str(workspace_id),
                        "required_role": required_role,
                    },
                )
                return False, None
            elif response.status_code == 404:
                logger.warning(
                    "Workspace not found",
                    extra={
                        "operation": "workspace_authorize",
                        "workspace_id": str(workspace_id),
                    },
                )
                return False, None
            else:
                try:
                    response_body = response.text
                except Exception:
                    response_body = "unable to read"

                logger.error(
                    f"Unexpected response from workspace_service: {response.status_code}",
                    extra={
                        "operation": "workspace_authorize",
                        "user_id": user_id,
                        "workspace_id": str(workspace_id),
                        "status_code": response.status_code,
                        "response_body": response_body[:500],
                        "headers": dict(response.headers),
                    },
                )
                return False, None

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout while authorizing user in workspace: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": "TimeoutException",
                    "traceback": traceback.format_exc(),
                },
            )
            return False, None
        except httpx.RequestError as e:
            logger.error(
                f"Request error while authorizing user: {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc(),
                },
            )
            return False, None
        except Exception as e:
            logger.error(
                f"Unexpected error while authorizing user: {e.__class__.__name__} - {e}",
                extra={
                    "operation": "workspace_authorize",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc(),
                },
            )
            return False, None

    def get_user_role(self, workspace_id: UUID, user_id: int) -> Optional[str]:
        """Get user's role in workspace."""
        try:
            url = f"{self.base_url}/internal/workspaces/{workspace_id}/role/{user_id}"
            response = self.client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                return data.get("role")
            return None
        except Exception as e:
            logger.error(
                f"Error getting user role: {e}",
                extra={
                    "operation": "get_user_role",
                    "user_id": user_id,
                    "workspace_id": str(workspace_id),
                },
            )
            return None


    def create_personal_workspace(
        self,
        user_id: int,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Optional[UUID]:
        """
        Create a personal workspace for a new user.
        Used by user_service during registration.
        """
        import time

        url = f"{self.base_url}/internal/workspaces/create-personal"
        payload = {"user_id": user_id}

        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    url, json=payload, headers=self._get_headers()
                )
                if response.status_code == 201:
                    data = response.json()
                    ws_id = data.get("workspace_id")
                    if ws_id:
                        logger.info(
                            f"Personal workspace created for user {user_id}",
                            extra={"operation": "create_personal_workspace", "user_id": user_id, "workspace_id": ws_id},
                        )
                        return UUID(ws_id)
                    return None
                else:
                    logger.warning(
                        f"Failed to create personal workspace: status={response.status_code}",
                        extra={"operation": "create_personal_workspace", "user_id": user_id, "status_code": response.status_code},
                    )
                    return None
            except httpx.ConnectError as e:
                logger.warning(
                    f"Workspace service connection error (attempt {attempt + 1}/{max_retries}): {e}",
                    extra={"operation": "create_personal_workspace", "user_id": user_id, "attempt": attempt + 1},
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
            except httpx.RequestError as e:
                logger.error(
                    f"Request error creating personal workspace: {e}",
                    extra={"operation": "create_personal_workspace", "user_id": user_id},
                )
                return None
            except Exception as e:
                logger.error(
                    f"Unexpected error creating personal workspace: {e}",
                    extra={"operation": "create_personal_workspace", "user_id": user_id},
                )
                return None
        return None

    def get_user_default_workspace(self, user_id: int) -> Optional[UUID]:
        """Get user's default workspace UUID."""
        try:
            url = f"{self.base_url}/internal/workspaces/default/{user_id}"
            response = self.client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                ws_id = data.get("workspace_id")
                if ws_id:
                    return UUID(ws_id)
                return None
            elif response.status_code == 404:
                logger.info(
                    f"No default workspace for user {user_id}",
                    extra={"operation": "get_default_workspace", "user_id": user_id},
                )
                return None
            else:
                logger.warning(
                    f"Unexpected response getting default workspace: {response.status_code}",
                    extra={"operation": "get_default_workspace", "user_id": user_id, "response_text": response.text[:500]},
                )
                return None
        except httpx.TimeoutException as e:
            logger.error(f"Timeout getting default workspace for user {user_id}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error getting default workspace for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting default workspace for user {user_id}: {e}")
            return None

    def close(self):
        self.client.close()
