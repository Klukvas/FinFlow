"""
Unified UserServiceClient for fetching user data (base currency, etc.).

Replaces 5 per-service app/clients/user_service_client.py files.
"""

import os
from typing import Optional

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CURRENCY = "USD"


class UserServiceClient:
    """Client for user_service internal API."""

    def __init__(self):
        self.base_url = os.environ.get("USER_SERVICE_URL", "http://user_service:8000")
        self.internal_token = os.environ.get("INTERNAL_SECRET_TOKEN", "")
        self.default_currency = os.environ.get("DEFAULT_CURRENCY", DEFAULT_CURRENCY)
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _get_headers(self) -> dict:
        headers: dict = {}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def get_user_base_currency(self, user_id: int) -> str:
        """
        Get user's base currency from user service.
        Falls back to DEFAULT_CURRENCY on any error.
        """
        try:
            response = self.client.get(
                f"/internal/users/{user_id}",
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("base_currency", self.default_currency)
            else:
                logger.warning(f"Failed to fetch user currency: {response.status_code}")
                return self.default_currency
        except Exception as e:
            logger.error(f"Error calling user service: {e}")
            return self.default_currency

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get full user data. Returns None on error or 404."""
        try:
            response = self.client.get(
                f"/internal/users/{user_id}",
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                return response.json()
            if response.status_code == 404:
                logger.warning(f"User {user_id} not found")
                return None
            logger.warning(f"Failed to fetch user {user_id}: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error calling user service for user {user_id}: {e}")
            return None

    def close(self):
        self.client.close()
