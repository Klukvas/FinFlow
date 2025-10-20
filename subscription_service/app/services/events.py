from __future__ import annotations

import json
import logging
import redis
from typing import Optional

from ..config import settings


logger = logging.getLogger("subscription_service.events")


class EventBus:
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        self.redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)

    def publish_subscription_changed(self, *, user_id: str, plan_code: str, status: str, expires_at: str, version: int) -> None:
        payload = {
            "user_id": user_id,
            "plan_code": plan_code,
            "status": status,
            "expires_at": expires_at,
            "version": version,
        }
        channel = "user.subscription.changed"
        self.redis.publish(channel, json.dumps(payload))
        logger.info("event_published", extra={"channel": channel, **payload})


