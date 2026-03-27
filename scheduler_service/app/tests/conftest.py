"""Shared fixtures for scheduler_service tests.

Provides:
- In-memory SQLite database with all models
- Mock HTTP clients (subscription, payment)
- Mock Redis / distributed lock
- Patched settings so real env vars are never required
- FastAPI test client with the scheduler mocked out
"""
from __future__ import annotations

import importlib
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from types import ModuleType
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# 1. Mock the ``shared`` package before any application code can import it.
#    The shared package is installed via pip in Docker but is not available
#    locally in the test environment.
# ---------------------------------------------------------------------------
if "shared" not in sys.modules:
    _shared_mod = ModuleType("shared")
    _shared_geoip_mod = ModuleType("shared.geoip")
    _shared_sentry_mod = ModuleType("shared.sentry")
    _shared_sentry_mod.init_sentry = MagicMock()  # type: ignore[attr-defined]

    class _NoOpMiddleware:
        """Dummy GeoIPMiddleware that does nothing."""
        def __init__(self, app, **kwargs):
            self.app = app

        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)

    _shared_geoip_mod.GeoIPMiddleware = _NoOpMiddleware  # type: ignore[attr-defined]
    _shared_mod.geoip = _shared_geoip_mod  # type: ignore[attr-defined]
    _shared_mod.sentry = _shared_sentry_mod  # type: ignore[attr-defined]

    sys.modules["shared"] = _shared_mod
    sys.modules["shared.geoip"] = _shared_geoip_mod
    sys.modules["shared.sentry"] = _shared_sentry_mod

# ---------------------------------------------------------------------------
# 2. Build a mock ``settings`` object and inject a pre-built ``app.config``
#    module into sys.modules BEFORE it can be imported normally.
#    This prevents pydantic from requiring real env vars.
# ---------------------------------------------------------------------------
_mock_settings = MagicMock()
_mock_settings.app_name = "scheduler_service_test"
_mock_settings.DATABASE_URL = "sqlite:///:memory:"
_mock_settings.REDIS_URL = "redis://localhost:6379/0"
_mock_settings.log_level = "DEBUG"
_mock_settings.internal_secret_token = "test-secret-token-12345"
_mock_settings.subscription_service_url = "http://localhost:8080"
_mock_settings.payment_service_url = "http://localhost:8000"
_mock_settings.scheduler_timezone = "UTC"
_mock_settings.renewal_check_cron = "0 */1 * * *"
_mock_settings.renewal_window_days = 1
_mock_settings.max_retry_attempts = 3
_mock_settings.retry_delay_seconds = 300
_mock_settings.job_max_instances = 1
_mock_settings.job_coalesce = True
_mock_settings.job_misfire_grace_time = 300

if "app.config" not in sys.modules:
    _config_mod = ModuleType("app.config")
    _config_mod.settings = _mock_settings  # type: ignore[attr-defined]
    _config_mod.Settings = MagicMock  # type: ignore[attr-defined]
    sys.modules["app.config"] = _config_mod
else:
    sys.modules["app.config"].settings = _mock_settings  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# 3. Pre-build the ``app.database`` module with a lightweight SQLite engine
#    so that the production module (which uses PostgreSQL-specific options
#    like pool_size / max_overflow) is never imported.
# ---------------------------------------------------------------------------
from sqlalchemy.ext.declarative import declarative_base as _declarative_base

_test_engine = create_engine("sqlite:///:memory:")
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_TestBase = _declarative_base()

if "app.database" not in sys.modules:
    _db_mod = ModuleType("app.database")
    _db_mod.engine = _test_engine  # type: ignore[attr-defined]
    _db_mod.SessionLocal = _TestSessionLocal  # type: ignore[attr-defined]
    _db_mod.Base = _TestBase  # type: ignore[attr-defined]
    _db_mod.get_db = MagicMock  # type: ignore[attr-defined]
    sys.modules["app.database"] = _db_mod

# ---------------------------------------------------------------------------
# 4. Monkey-patch PostgreSQL JSONB / UUID to use SQLite-compatible types
#    BEFORE models are imported.
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy import String, Text

# Override JSONB to use plain JSON (SQLite-compatible)
import sqlalchemy.dialects.postgresql as pg_dialects

_original_jsonb_init = JSONB.__init__


def _patched_jsonb_init(self, *args, **kwargs):
    """Make JSONB behave as plain JSON for SQLite."""
    JSON.__init__(self)


# Instead of patching __init__, we override at the column level.
# The cleanest approach: register a type adapter with SQLite dialect.
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

if not hasattr(SQLiteTypeCompiler, 'visit_JSONB'):
    SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

if not hasattr(SQLiteTypeCompiler, 'visit_UUID'):
    SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "VARCHAR(36)"

# Also need to handle DDL-level compilation for these types.
from sqlalchemy.dialects.sqlite.base import SQLiteDDLCompiler

# Now safe to import application modules that reference ``settings`` and ``database``.
from app.database import Base  # noqa: E402
from app.models.models import JobExecution, RenewalAttempt, JobStatus  # noqa: E402
from app.repositories.job_repository import JobRepository  # noqa: E402


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """Provide a transactional DB session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def job_repo(db_session):
    """JobRepository backed by the in-memory session."""
    return JobRepository(db_session)


# ---------------------------------------------------------------------------
# Mock client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_subscription_client():
    """AsyncMock for SubscriptionClient with sensible defaults."""
    client = AsyncMock()
    client.get_expiring_subscriptions = AsyncMock(return_value=[])
    client.extend_subscription = AsyncMock(return_value={"status": "extended"})
    client.mark_subscription_past_due = AsyncMock(return_value={"status": "past_due"})
    return client


@pytest.fixture()
def mock_payment_client():
    """AsyncMock for PaymentClient with sensible defaults."""
    client = AsyncMock()
    client.create_recurring_payment = AsyncMock(
        return_value={
            "payment_id": str(uuid.uuid4()),
            "status": "PAID",
        }
    )
    client.get_payment_status = AsyncMock(
        return_value={"status": "PAID"}
    )
    return client


@pytest.fixture()
def mock_distributed_lock():
    """AsyncMock for DistributedLock that always acquires."""
    lock = AsyncMock()
    lock.acquire = AsyncMock(return_value=True)
    lock.release = AsyncMock(return_value=True)
    return lock


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def make_subscription(
    subscription_id: int = 1,
    user_id: str = "user-abc",
    plan_code: str = "pro_monthly",
    plan_amount: str = "199.00",
    currency: str = "UAH",
    auto_renew: bool = True,
    recurring_token: str = "tok_abc123",
    payment_provider: str = "MONOBANK",
    **overrides: Any,
) -> Dict[str, Any]:
    """Build a subscription dict matching the shape returned by subscription_service."""
    data = {
        "id": subscription_id,
        "user_id": user_id,
        "plan_code": plan_code,
        "plan_amount": plan_amount,
        "currency": currency,
        "auto_renew": auto_renew,
        "recurring_token": recurring_token,
        "payment_provider": payment_provider,
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_client():
    """Provide a synchronous TestClient for the FastAPI app.

    The scheduler is stubbed out so that the lifespan does not require
    a real APScheduler or Redis.
    """
    mock_scheduler = MagicMock()
    mock_scheduler.running = True
    mock_scheduler.get_jobs.return_value = []
    mock_scheduler.get_job.return_value = None

    from starlette.testclient import TestClient
    from app.main import app
    import app.main as main_module

    original_scheduler = main_module.scheduler
    main_module.scheduler = mock_scheduler

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, mock_scheduler

    main_module.scheduler = original_scheduler
