import logging
from typing import Optional
from uuid import UUID

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SERVICE_URLS: dict[str, str] = {
    "expenses": settings.EXPENSE_SERVICE_URL,
    "incomes": settings.INCOME_SERVICE_URL,
    "debts": settings.DEBT_SERVICE_URL,
    "goals": settings.GOALS_SERVICE_URL,
    "accounts": settings.ACCOUNT_SERVICE_URL,
    "categories": settings.CATEGORY_SERVICE_URL,
    "recurring": settings.RECURRING_SERVICE_URL,
}

ENDPOINT_PATHS: dict[str, str] = {
    "expenses": "/internal/expenses/ai-summary",
    "incomes": "/internal/incomes/ai-summary",
    "debts": "/internal/debts/ai-summary",
    "goals": "/internal/goals/ai-summary",
    "accounts": "/internal/accounts/ai-summary",
    "categories": "/internal/categories/ai-summary",
    "recurring": "/internal/recurring/ai-summary",
}


async def fetch_data(
    source: str,
    user_id: int,
    workspace_id: UUID,
) -> Optional[dict]:
    """Fetch AI summary data from a single internal service."""
    base_url = SERVICE_URLS.get(source)
    path = ENDPOINT_PATHS.get(source)
    if not base_url or not path:
        logger.error(f"Unknown data source: {source}")
        return None

    url = f"{base_url}{path}"
    headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
    params = {"user_id": str(user_id), "workspace_id": str(workspace_id)}

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched {source} data: {len(data.get('items', []))} items")
                return data
            logger.warning(f"Failed to fetch {source}: status={response.status_code}")
            return None
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {source} from {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {source}: {e}")
        return None
