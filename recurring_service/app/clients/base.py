import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseServiceClient:
    """Базовый клиент для взаимодействия с другими сервисами"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Выполнить HTTP запрос к сервису"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json", "X-Internal-Token": settings.INTERNAL_SECRET}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error for {method} {url}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error for {method} {url}: {str(e)}")
                raise

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET запрос"""
        return await self._make_request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST запрос"""
        return await self._make_request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PUT запрос"""
        return await self._make_request("PUT", endpoint, data=data)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE запрос"""
        return await self._make_request("DELETE", endpoint)
