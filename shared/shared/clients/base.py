"""
Base HTTP client with retry logic for inter-service communication.

Replaces per-service app/clients/base.py files.
"""

import os
import time
from typing import Optional, Dict

import httpx

from shared.logging import get_logger, log_external_service_call


class BaseHttpClient:
    """HTTP client with retry logic and structured logging."""

    def __init__(
        self,
        base_url: str,
        timeout: Optional[float] = None,
        retry_attempts: Optional[int] = None,
    ):
        self.base_url = base_url
        self.timeout = timeout or float(os.environ.get("HTTP_TIMEOUT", "10.0"))
        self.retry_attempts = retry_attempts or int(os.environ.get("HTTP_RETRY_ATTEMPTS", "3"))
        self.logger = get_logger(__name__)

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _get_internal_headers(self) -> Dict[str, str]:
        """Get headers with internal service token."""
        headers = {"Content-Type": "application/json"}
        token = os.environ.get("INTERNAL_SECRET_TOKEN", "")
        if token:
            headers["X-Internal-Token"] = token
        return headers

    def _make_request_with_retry(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with retry logic and exponential backoff."""
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                response = self.client.request(method, path, headers=headers, **kwargs)
                duration = (time.time() - start_time) * 1000

                log_external_service_call(
                    self.logger,
                    self.base_url,
                    f"{method} {path}",
                    response.status_code,
                    duration,
                )

                return response

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    break

        self.logger.error(f"All {self.retry_attempts} attempts failed for {method} {path}")
        raise ExternalServiceError(
            service=self.base_url,
            detail=f"Request failed after {self.retry_attempts} attempts: {last_exception}",
        )

    def get(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        return self._make_request_with_retry("GET", path, headers, **kwargs)

    def post(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        return self._make_request_with_retry("POST", path, headers, **kwargs)

    def put(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        return self._make_request_with_retry("PUT", path, headers, **kwargs)

    def delete(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        return self._make_request_with_retry("DELETE", path, headers, **kwargs)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ExternalServiceError(Exception):
    """Raised when an external service call fails after all retries."""

    def __init__(self, service: str, detail: str):
        self.service = service
        self.detail = detail
        super().__init__(f"External service error ({service}): {detail}")
