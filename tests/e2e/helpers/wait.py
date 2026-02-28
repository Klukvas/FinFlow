"""Health check utilities for waiting on services."""
from __future__ import annotations

import asyncio
import httpx


SERVICE_HEALTH_ENDPOINTS: dict[str, str] = {
    "user_service": "http://localhost:8001/health",
    "workspace_service": "http://localhost:8012/health",
    "category_service": "http://localhost:8002/health",
    "expense_service": "http://localhost:8003/health",
    "income_service": "http://localhost:8004/health",
    "account_service": "http://localhost:8009/health",
    "subscription_service": "http://localhost:8011/health",
    "ai_assistant_service": "http://localhost:8015/health",
}


async def check_service(url: str, *, timeout: float = 5.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return resp.status_code == 200
    except Exception:
        return False


async def wait_for_services(*, max_wait: float = 120.0, poll_interval: float = 3.0) -> None:
    """Block until all services respond to health checks."""
    elapsed = 0.0
    while elapsed < max_wait:
        results = {name: await check_service(url) for name, url in SERVICE_HEALTH_ENDPOINTS.items()}
        if all(results.values()):
            return
        unhealthy = [n for n, ok in results.items() if not ok]
        print(f"[{elapsed:.0f}s] Waiting for: {', '.join(unhealthy)}")
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    results = {name: await check_service(url) for name, url in SERVICE_HEALTH_ENDPOINTS.items()}
    unhealthy = [n for n, ok in results.items() if not ok]
    if unhealthy:
        raise TimeoutError(f"Services not ready after {max_wait}s: {', '.join(unhealthy)}")
