import calendar
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.services.cache_service import get_redis

logger = logging.getLogger(__name__)

PLAN_QUOTAS: dict[str, int] = {
    "professional": settings.MONTHLY_QUOTA_PROFESSIONAL,
    "enterprise": settings.MONTHLY_QUOTA_ENTERPRISE,
}


def _usage_key(user_id: int, workspace_id: str) -> str:
    """Global key per user+workspace per month (no prompt_id)."""
    now = datetime.now(timezone.utc)
    return f"ai_usage:{user_id}:{workspace_id}:{now.year}:{now.month}"


def _seconds_until_month_end() -> int:
    """Seconds remaining until the end of the current month."""
    now = datetime.now(timezone.utc)
    _, last_day = calendar.monthrange(now.year, now.month)
    end_of_month = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    return max(int((end_of_month - now).total_seconds()), 1)


async def check_rate_limit(
    user_id: int, workspace_id: str, plan_code: str
) -> Optional[int]:
    """Check if user has remaining quota.

    Returns None if allowed, or remaining seconds until reset if quota exhausted.
    """
    quota = PLAN_QUOTAS.get(plan_code)
    if quota is None:
        logger.warning(f"Unknown plan code '{plan_code}' for rate limit, denying")
        return _seconds_until_month_end()

    try:
        client = await get_redis()
        key = _usage_key(user_id, workspace_id)
        used = await client.get(key)
        used_count = int(used) if used else 0

        if used_count >= quota:
            ttl = _seconds_until_month_end()
            logger.info(
                f"Quota exhausted for user={user_id}: "
                f"used={used_count}/{quota}, resets in {ttl}s"
            )
            return ttl
        return None
    except Exception as e:
        logger.error(f"Rate limit check error — failing closed: {e}")
        return 60


async def increment_usage(user_id: int, workspace_id: str) -> None:
    """Increment usage counter after successful analysis."""
    try:
        client = await get_redis()
        key = _usage_key(user_id, workspace_id)
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, _seconds_until_month_end())
        await pipe.execute()
        logger.info(f"Usage incremented for user={user_id}")
    except Exception as e:
        logger.warning(f"Usage increment error: {e}")


async def decrement_usage(user_id: int, workspace_id: str) -> None:
    """Decrement usage counter (refund after failed analysis). Atomic via Lua script."""
    try:
        client = await get_redis()
        key = _usage_key(user_id, workspace_id)
        # Atomic decrement that clamps at 0 to avoid race conditions
        lua_script = """
        local current = tonumber(redis.call('GET', KEYS[1]) or '0')
        if current > 0 then
            redis.call('DECR', KEYS[1])
            return 1
        end
        return 0
        """
        result = await client.eval(lua_script, 1, key)
        if result == 1:
            logger.info(f"Usage decremented (refund) for user={user_id}")
    except Exception as e:
        logger.warning(f"Usage decrement error: {e}")


async def get_usage_info(user_id: int, workspace_id: str, plan_code: str) -> dict:
    """Get current usage info for the user."""
    quota = PLAN_QUOTAS.get(plan_code, 0)
    try:
        client = await get_redis()
        key = _usage_key(user_id, workspace_id)
        used = await client.get(key)
        used_count = int(used) if used else 0
        return {
            "used": used_count,
            "quota": quota,
            "remaining": max(quota - used_count, 0),
            "resets_in": _seconds_until_month_end(),
        }
    except Exception as e:
        logger.warning(f"Usage info error: {e}")
        return {
            "used": 0,
            "quota": quota,
            "remaining": quota,
            "resets_in": _seconds_until_month_end(),
        }
