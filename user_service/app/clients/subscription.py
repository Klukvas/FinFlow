from __future__ import annotations

import httpx
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.SUBSCRIPTION_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def set_basic_plan(self, user_id: int, plan_code: str = "basic") -> None:
        url = f"{self.base_url}/v1/subscriptions/{user_id}:set_plan"
        headers = {
            "Idempotency-Key": f"user-{user_id}-bootstrap",
            "X-Internal-Token": settings.INTERNAL_SECRET_TOKEN or "",
        }
        payload = {"plan_code": plan_code}
        try:
            resp = self.client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logger.warning(f"Failed to set {plan_code} plan for user {user_id}: status={resp.status_code}")
                return
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Subscription service unreachable when setting plan for user {user_id}: {e}")
            return
        except Exception as e:
            logger.error(f"Error setting plan for user {user_id}: {e}")
            return
