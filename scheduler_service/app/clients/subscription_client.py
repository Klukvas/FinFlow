from __future__ import annotations

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger("scheduler_service.subscription_client")


class SubscriptionClient:
    """Client for subscription_service"""

    def __init__(self):
        self.base_url = settings.subscription_service_url
        self.internal_token = settings.internal_secret_token

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for internal API calls"""
        return {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }

    async def get_expiring_subscriptions(
        self, days_ahead: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get subscriptions that are expiring soon
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of subscription records
        """
        url = f"{self.base_url}/v1/internal/subscriptions:expiring"
        params = {"days_ahead": days_ahead}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url, params=params, headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Retrieved {len(data)} expiring subscriptions",
                    extra={"count": len(data), "days_ahead": days_ahead},
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to get expiring subscriptions: {e}",
                extra={"error": str(e)},
            )
            raise

    async def extend_subscription(
        self, subscription_id: int, payment_id: str
    ) -> Dict[str, Any]:
        """
        Extend subscription after successful payment
        
        Args:
            subscription_id: Subscription ID
            payment_id: Payment ID that triggered extension
            
        Returns:
            Updated subscription data
        """
        url = f"{self.base_url}/v1/internal/subscriptions/{subscription_id}:extend"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"payment_id": payment_id},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Extended subscription {subscription_id}",
                    extra={
                        "subscription_id": subscription_id,
                        "payment_id": payment_id,
                        "new_expires_at": data.get("expires_at"),
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to extend subscription {subscription_id}: {e}",
                extra={
                    "subscription_id": subscription_id,
                    "payment_id": payment_id,
                    "error": str(e),
                },
            )
            raise

    async def mark_subscription_past_due(
        self, subscription_id: int, reason: str
    ) -> Dict[str, Any]:
        """
        Mark subscription as past due after failed payment
        
        Args:
            subscription_id: Subscription ID
            reason: Failure reason
            
        Returns:
            Updated subscription data
        """
        url = f"{self.base_url}/v1/internal/subscriptions/{subscription_id}:mark_past_due"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"reason": reason},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Marked subscription {subscription_id} as past_due",
                    extra={
                        "subscription_id": subscription_id,
                        "reason": reason,
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to mark subscription {subscription_id} as past_due: {e}",
                extra={
                    "subscription_id": subscription_id,
                    "error": str(e),
                },
            )
            raise
