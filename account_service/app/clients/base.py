import httpx
from typing import Optional, Dict, Any
import time
from app.config import settings
from app.utils.logger import get_logger, log_external_service_call
from app.exceptions import ExternalServiceError

class BaseHttpClient:
    def __init__(self, base_url: str, timeout: float = None, retry_attempts: int = None):
        self.base_url = base_url
        self.timeout = timeout or settings.http_timeout
        self.retry_attempts = retry_attempts or settings.http_retry_attempts
        self.logger = get_logger(__name__)
        
        # Create client with proper configuration
        self.client = httpx.Client(
            base_url=self.base_url, 
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    def _make_request_with_retry(self, method: str, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                response = self.client.request(method, path, headers=headers, **kwargs)
                duration = time.time() - start_time
                
                log_external_service_call(
                    self.logger, 
                    self.base_url, 
                    f"{method} {path}", 
                    response.status_code, 
                    duration
                )
                
                return response
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    break
        
        # All retries failed
        self.logger.error(f"All {self.retry_attempts} attempts failed for {method} {path}")
        raise ExternalServiceError(
            service=self.base_url,
            detail=f"Request failed after {self.retry_attempts} attempts: {last_exception}"
        )

    def get(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make GET request with retry logic"""
        return self._make_request_with_retry("GET", path, headers, **kwargs)

    def post(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make POST request with retry logic"""
        return self._make_request_with_retry("POST", path, headers, **kwargs)

    def put(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make PUT request with retry logic"""
        return self._make_request_with_retry("PUT", path, headers, **kwargs)

    def delete(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make DELETE request with retry logic"""
        return self._make_request_with_retry("DELETE", path, headers, **kwargs)

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
