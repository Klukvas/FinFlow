import json
import logging
from typing import Optional

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def _cache_key(workspace_id: str, prompt_id: str, language: str, data_hash: str) -> str:
    return f"ai:{workspace_id}:{prompt_id}:{language}:{data_hash}"


async def get_cached_result(
    workspace_id: str, prompt_id: str, language: str, data_hash: str
) -> Optional[dict]:
    try:
        client = await get_redis()
        key = _cache_key(workspace_id, prompt_id, language, data_hash)
        raw = await client.get(key)
        if raw is not None:
            logger.info(f"Cache hit for key={key}")
            return json.loads(raw)
        return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


async def set_cached_result(
    workspace_id: str, prompt_id: str, language: str, data_hash: str, result: dict
) -> None:
    try:
        client = await get_redis()
        key = _cache_key(workspace_id, prompt_id, language, data_hash)
        await client.set(key, json.dumps(result), ex=settings.CACHE_TTL)
        logger.info(f"Cache set for key={key}, TTL={settings.CACHE_TTL}s")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


def _latest_key(workspace_id: str, prompt_id: str, language: str) -> str:
    return f"ai_latest:{workspace_id}:{prompt_id}:{language}"


async def get_latest_result(
    workspace_id: str, prompt_id: str, language: str
) -> Optional[dict]:
    """Get the most recent analysis result regardless of data hash."""
    try:
        client = await get_redis()
        key = _latest_key(workspace_id, prompt_id, language)
        raw = await client.get(key)
        if raw is not None:
            logger.info(f"Latest result hit for key={key}")
            return json.loads(raw)
        return None
    except Exception as e:
        logger.warning(f"Latest result read error: {e}")
        return None


async def set_latest_result(
    workspace_id: str, prompt_id: str, language: str, result: dict
) -> None:
    """Store the most recent analysis result for retrieval when user returns."""
    try:
        client = await get_redis()
        key = _latest_key(workspace_id, prompt_id, language)
        await client.set(key, json.dumps(result), ex=settings.CACHE_TTL)
        logger.info(f"Latest result set for key={key}, TTL={settings.CACHE_TTL}s")
    except Exception as e:
        logger.warning(f"Latest result write error: {e}")
