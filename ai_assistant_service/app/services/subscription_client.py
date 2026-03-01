import asyncio
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY = 0.5


async def check_feature_access(user_id: int) -> tuple[Optional[str], Optional[int]]:
    """Check if user has AI assistant feature access.

    Returns (plan_code, limit_value) if allowed.
    - limit_value is the monthly quota from subscription (None = unlimited).
    Returns (None, None) if denied.

    Retries once on transient network errors to avoid blocking paid users
    during brief subscription service restarts.
    """
    url = f"{settings.SUBSCRIPTION_SERVICE_URL.rstrip('/')}/v1/internal/features/{user_id}"
    headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}

    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Subscription service returned {resp.status_code} for user {user_id}")
                    return None, None

                features = resp.json()
                if not isinstance(features, list):
                    logger.error(f"Unexpected subscription response type for user {user_id}")
                    return None, None
                features_dict = {f["feature_code"]: f for f in features if isinstance(f, dict)}

                ai_feature = features_dict.get("ai_assistant", {})
                if not ai_feature.get("enabled", False):
                    logger.info(f"AI assistant feature disabled for user {user_id}")
                    return None, None

                plan_code = ai_feature.get("plan_code", "")
                limit_value = ai_feature.get("limit_value")
                # limit_value: int = monthly quota, None = unlimited
                return plan_code, limit_value

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Subscription check attempt {attempt + 1} failed for user {user_id}: {e}. Retrying..."
                )
                await asyncio.sleep(RETRY_DELAY)

    logger.error(f"Error checking subscription for user {user_id} after {MAX_RETRIES} attempts: {last_error}")
    return None, None
