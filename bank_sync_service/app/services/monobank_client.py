import asyncio
import hashlib
import time

import httpx

from app.config import settings
from app.exceptions import MonobankApiError, RateLimitError
from app.schemas.monobank import MonobankClientInfo, MonobankStatementItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ISO 4217 numeric code → alphabetic code
CURRENCY_MAP = {
    980: "UAH",
    840: "USD",
    978: "EUR",
    826: "GBP",
    985: "PLN",
    203: "CZK",
    756: "CHF",
    392: "JPY",
    156: "CNY",
    949: "TRY",
    376: "ILS",
    784: "AED",
}


def numeric_to_alpha_currency(code: int) -> str:
    return CURRENCY_MAP.get(code, str(code))


class MonobankClient:
    def __init__(self):
        self.base_url = settings.MONOBANK_API_BASE_URL
        self.rate_limit_seconds = settings.MONOBANK_RATE_LIMIT_SECONDS
        self._last_request_time: dict[str, float] = {}

    @staticmethod
    def _token_key(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    def _check_rate_limit(self, token: str) -> None:
        key = self._token_key(token)
        now = time.time()
        last = self._last_request_time.get(key, 0)
        elapsed = now - last
        if elapsed < self.rate_limit_seconds:
            remaining = int(self.rate_limit_seconds - elapsed) + 1
            raise RateLimitError(remaining)

    async def wait_for_rate_limit(self, token: str) -> None:
        """Wait until rate limit window expires instead of raising."""
        key = self._token_key(token)
        now = time.time()
        last = self._last_request_time.get(key, 0)
        elapsed = now - last
        if elapsed < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - elapsed + 1
            logger.info(f"Rate limit: waiting {wait_time:.0f}s before next Monobank request")
            await asyncio.sleep(wait_time)

    def _record_request(self, token: str) -> None:
        self._last_request_time[self._token_key(token)] = time.time()

    async def get_client_info(self, token: str) -> MonobankClientInfo:
        self._check_rate_limit(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/personal/client-info",
                    headers={"X-Token": token},
                )
                self._record_request(token)

                if response.status_code == 403:
                    raise MonobankApiError("Invalid Monobank token or insufficient permissions")
                if response.status_code == 429:
                    raise RateLimitError(self.rate_limit_seconds)

                response.raise_for_status()
                return MonobankClientInfo(**response.json())

            except (RateLimitError, MonobankApiError):
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Monobank API HTTP error: {e.response.status_code}")
                raise MonobankApiError(f"Monobank API returned status {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Monobank API request error: {str(e)}")
                raise MonobankApiError(f"Failed to connect to Monobank API: {str(e)}")

    async def get_statements(
        self,
        token: str,
        account_id: str,
        from_ts: int,
        to_ts: int,
    ) -> list[MonobankStatementItem]:
        self._check_rate_limit(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/personal/statement/{account_id}/{from_ts}/{to_ts}",
                    headers={"X-Token": token},
                )
                self._record_request(token)

                if response.status_code == 429:
                    raise RateLimitError(self.rate_limit_seconds)

                response.raise_for_status()
                data = response.json()
                return [MonobankStatementItem(**item) for item in data]

            except (RateLimitError, MonobankApiError):
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Monobank statements HTTP error: {e.response.status_code}")
                raise MonobankApiError(f"Failed to fetch statements: status {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Monobank statements request error: {str(e)}")
                raise MonobankApiError(f"Failed to connect to Monobank API: {str(e)}")

    async def set_webhook(self, token: str, url: str) -> bool:
        self._check_rate_limit(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/personal/webhook",
                    headers={"X-Token": token},
                    json={"webHookUrl": url},
                )
                self._record_request(token)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to set Monobank webhook: {str(e)}")
                return False


# Singleton
monobank_client = MonobankClient()
