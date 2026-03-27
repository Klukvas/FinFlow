import os
import sys
from types import ModuleType
from unittest.mock import MagicMock

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("CURRENCY_API_URL", "https://api.exchangerate-api.com/v4/latest")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-secret-token-for-testing")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")

# ---------------------------------------------------------------------------
# Mock the 'shared' package and its submodules before any app imports.
# The shared package is installed separately in production but not available
# in the isolated test environment.
# ---------------------------------------------------------------------------

# We need a real BaseHTTPMiddleware subclass for GeoIPMiddleware
# so that FastAPI can mount it properly during app startup.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from contextvars import ContextVar

_country_code_var = ContextVar("country_code", default=None)


class _StubGeoIPMiddleware(BaseHTTPMiddleware):
    """No-op middleware that replaces the real GeoIPMiddleware in tests."""

    async def dispatch(self, request, call_next) -> Response:
        return await call_next(request)


# Build the shared.geoip module with the real middleware class
_geoip_module = ModuleType("shared.geoip")
_geoip_module.GeoIPMiddleware = _StubGeoIPMiddleware
_geoip_module.geoip_reader = MagicMock()
_geoip_module.GeoIPReader = MagicMock()
_geoip_module.get_country_code = MagicMock(return_value=None)

# Build the shared.logging sub-modules
_logger_module = ModuleType("shared.logging.logger")
_logger_module.configure = MagicMock()
_logger_module.get_logger = MagicMock(return_value=MagicMock())
_logger_module.log_security_event = MagicMock()
_logger_module.log_operation = MagicMock()
_logger_module.log_authentication_attempt = MagicMock()
_logger_module.log_external_service_call = MagicMock()

_logging_utils_module = ModuleType("shared.logging.logging_utils")
_logging_utils_module.set_request_context = MagicMock()
_logging_utils_module.clear_request_context = MagicMock()
_logging_utils_module.generate_request_id = MagicMock(return_value="test-request-id")
_logging_utils_module.country_code_var = _country_code_var

_logging_module = ModuleType("shared.logging")
_logging_module.logger = _logger_module
_logging_module.logging_utils = _logging_utils_module

_sentry_module = ModuleType("shared.sentry")
_sentry_module.init_sentry = MagicMock()

_shared_module = ModuleType("shared")
_shared_module.geoip = _geoip_module
_shared_module.logging = _logging_module
_shared_module.sentry = _sentry_module

sys.modules["shared"] = _shared_module
sys.modules["shared.geoip"] = _geoip_module
sys.modules["shared.geoip.reader"] = MagicMock()
sys.modules["shared.geoip.middleware"] = MagicMock(GeoIPMiddleware=_StubGeoIPMiddleware)
sys.modules["shared.geoip.dependencies"] = MagicMock()
sys.modules["shared.logging"] = _logging_module
sys.modules["shared.logging.logger"] = _logger_module
sys.modules["shared.logging.logging_utils"] = _logging_utils_module
sys.modules["shared.sentry"] = _sentry_module

# ---------------------------------------------------------------------------
# Now it is safe to import the app
# ---------------------------------------------------------------------------

import pytest
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.currency import CurrencyService
from app.routers.currency import get_currency_service
from app.schemas.currency import CurrencyInfo


@pytest.fixture
def mock_redis():
    """Return a MagicMock that behaves like a Redis client."""
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.ping.return_value = True
    return redis_mock


@pytest.fixture
def mock_http_client():
    """Return an AsyncMock that behaves like httpx.AsyncClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def currency_service(mock_redis, mock_http_client):
    """Return a CurrencyService with mocked Redis and HTTP clients."""
    with patch("app.services.currency.redis.from_url", return_value=mock_redis):
        with patch("app.services.currency.httpx.AsyncClient", return_value=mock_http_client):
            service = CurrencyService()
    return service


@pytest.fixture
def sample_currencies():
    """Return a list of sample CurrencyInfo objects for testing."""
    return [
        CurrencyInfo(code="USD", name="US Dollar", symbol="$", flag="US", locale="en-US"),
        CurrencyInfo(code="EUR", name="Euro", symbol="E", flag="EU", locale="de-DE"),
        CurrencyInfo(code="GBP", name="British Pound", symbol="L", flag="GB", locale="en-GB"),
    ]


@pytest.fixture
def sample_rates():
    """Return a sample rates dictionary."""
    return {
        "EUR": 0.85,
        "GBP": 0.73,
        "JPY": 110.0,
        "CAD": 1.25,
        "AUD": 1.35,
        "CHF": 0.92,
        "CNY": 6.45,
        "UAH": 27.5,
        "RUB": 73.5,
        "USD": 1.0,
    }


@pytest.fixture
def mock_currency_service(sample_currencies, sample_rates):
    """Return a fully mocked CurrencyService for use in router tests."""
    service = AsyncMock(spec=CurrencyService)
    service.get_supported_currencies.return_value = sample_currencies
    service.cache_key_prefix = "currency:"
    service._fetch_currencies_from_api = AsyncMock(return_value=sample_currencies)
    service._get_fallback_currencies = MagicMock(return_value=sample_currencies)
    service._cache_currencies = AsyncMock()
    return service


@pytest.fixture
def client(mock_currency_service):
    """Return a TestClient with the CurrencyService dependency overridden."""
    from fastapi.testclient import TestClient

    def override_get_currency_service():
        return mock_currency_service

    app.dependency_overrides[get_currency_service] = override_get_currency_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
