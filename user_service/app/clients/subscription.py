from __future__ import annotations

import httpx
from typing import Optional
from app.config import settings


class SubscriptionClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.SUBSCRIPTION_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def set_basic_plan(self, user_id: int, plan_code: str = "basic") -> None:
        url = f"{self.base_url}/v1/subscriptions/{user_id}:set_plan"
        headers = {"Idempotency-Key": f"user-{user_id}-bootstrap"}
        payload = {"plan_code": plan_code}
        try:
            resp = self.client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                # Don't raise; registration should still succeed. Log upstream error.
                return
        except Exception:
            # Swallow errors to avoid breaking registration flow.
            return


