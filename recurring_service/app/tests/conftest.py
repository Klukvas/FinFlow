import os
import sys
import tempfile

# Create a temp file for the test database
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db", prefix="test_recurring_")
os.close(_test_db_fd)

_TEST_DB_URL = f"sqlite:///{_test_db_path}"

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-recurring")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token-recurring")
os.environ.setdefault("EXPENSE_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("INCOME_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8003")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8004")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")

# Patch database module BEFORE app.main imports it.
# The production database.py uses pool_size/max_overflow which are incompatible
# with SQLite's SingletonThreadPool, so we intercept and create a test-compatible engine.
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from types import ModuleType

SQLALCHEMY_DATABASE_URL = _TEST_DB_URL

_test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

_TestBase = declarative_base()

_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _test_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a fake database module and inject it before app.main is loaded
_db_mod = ModuleType("app.database")
_db_mod.engine = _test_engine
_db_mod.Base = _TestBase
_db_mod.SessionLocal = _TestSessionLocal
_db_mod.get_db = _test_get_db
sys.modules["app.database"] = _db_mod

# Now safe to import the rest of the application
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import UUID, uuid4

from app.main import app
from app.database import Base, get_db
from app.models.recurring_payment import RecurringPayment
from app.models.payment_schedule import PaymentSchedule

# Create all tables using the actual model metadata
Base.metadata.create_all(bind=_test_engine)

from app.dependencies import get_current_user_id, get_workspace_id, verify_internal_token

TEST_USER_ID = 1
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}
TEST_INTERNAL_TOKEN = "test-internal-token-recurring"

TestingSessionLocal = _TestSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    return TEST_USER_ID


def override_get_workspace_id():
    return TEST_WORKSPACE_ID


def override_verify_internal_token():
    return None


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id
app.dependency_overrides[get_workspace_id] = override_get_workspace_id
app.dependency_overrides[verify_internal_token] = override_verify_internal_token


@pytest.fixture(autouse=True)
def mock_workspace_authorize():
    """Auto-mock workspace authorization so all tests pass workspace checks."""
    with patch(
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner"),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_subscription_check():
    """Auto-mock subscription check so recurring creation is not blocked."""
    with patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
        return_value=True,
    ), patch(
        "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
        return_value=set(),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.get_user_features",
        return_value={"recurring": {"limit_value": 100}},
    ):
        yield


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database tables before and after each test for isolation."""
    db = TestingSessionLocal()
    try:
        db.query(PaymentSchedule).delete()
        db.query(RecurringPayment).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    yield

    db = TestingSessionLocal()
    try:
        db.query(PaymentSchedule).delete()
        db.query(RecurringPayment).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture
def db_session():
    """Provide a database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def internal_client():
    """Client with internal token header for internal endpoints."""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        c.headers["X-Internal-Token"] = TEST_INTERNAL_TOKEN
        yield c


@pytest.fixture
def sample_recurring_payment_data():
    """Valid recurring payment creation data."""
    return {
        "name": "Monthly Rent",
        "description": "Monthly rent payment",
        "amount": "1500.00",
        "currency": "USD",
        "category_id": 1,
        "payment_type": "EXPENSE",
        "schedule_type": "monthly",
        "schedule_config": {"day_of_month": 1},
        "start_date": "2025-01-01",
        "end_date": None,
    }


@pytest.fixture
def sample_weekly_payment_data():
    """Valid weekly recurring payment data."""
    return {
        "name": "Weekly Groceries",
        "description": "Weekly grocery shopping",
        "amount": "200.00",
        "currency": "USD",
        "category_id": 2,
        "payment_type": "EXPENSE",
        "schedule_type": "weekly",
        "schedule_config": {"day_of_week": 1},
        "start_date": "2025-01-06",
        "end_date": None,
    }


@pytest.fixture
def sample_daily_payment_data():
    """Valid daily recurring payment data."""
    return {
        "name": "Daily Coffee",
        "description": "Morning coffee",
        "amount": "5.00",
        "currency": "USD",
        "category_id": 3,
        "payment_type": "EXPENSE",
        "schedule_type": "daily",
        "schedule_config": {},
        "start_date": "2025-01-01",
        "end_date": None,
    }


@pytest.fixture
def sample_yearly_payment_data():
    """Valid yearly recurring payment data."""
    return {
        "name": "Annual Insurance",
        "description": "Annual insurance premium",
        "amount": "5000.00",
        "currency": "USD",
        "category_id": 4,
        "payment_type": "EXPENSE",
        "schedule_type": "yearly",
        "schedule_config": {"month": 6, "day": 15},
        "start_date": "2025-01-01",
        "end_date": None,
    }


@pytest.fixture
def sample_income_payment_data():
    """Valid income recurring payment data."""
    return {
        "name": "Monthly Salary",
        "description": "Monthly salary",
        "amount": "5000.00",
        "currency": "USD",
        "category_id": 5,
        "payment_type": "INCOME",
        "schedule_type": "monthly",
        "schedule_config": {"day_of_month": 25},
        "start_date": "2025-01-01",
        "end_date": None,
    }


@pytest.fixture
def created_recurring_payment(db_session):
    """Create a recurring payment directly in the database."""
    payment = RecurringPayment(
        id=uuid4(),
        user_id=TEST_USER_ID,
        workspace_id=TEST_WORKSPACE_ID,
        name="Test Payment",
        description="Test description",
        amount=Decimal("100.00"),
        currency="USD",
        category_id=1,
        payment_type="EXPENSE",
        schedule_type="monthly",
        schedule_config={"day_of_month": 15},
        start_date=date(2025, 1, 15),
        end_date=None,
        status="active",
        next_execution=date(2025, 1, 15),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def created_paused_payment(db_session):
    """Create a paused recurring payment directly in the database."""
    payment = RecurringPayment(
        id=uuid4(),
        user_id=TEST_USER_ID,
        workspace_id=TEST_WORKSPACE_ID,
        name="Paused Payment",
        description="A paused payment",
        amount=Decimal("50.00"),
        currency="USD",
        category_id=1,
        payment_type="EXPENSE",
        schedule_type="weekly",
        schedule_config={"day_of_week": 3},
        start_date=date(2025, 1, 1),
        end_date=None,
        status="paused",
        next_execution=date(2025, 1, 8),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def created_payment_with_schedule(db_session, created_recurring_payment):
    """Create a recurring payment with associated payment schedules."""
    schedule_executed = PaymentSchedule(
        id=uuid4(),
        recurring_payment_id=created_recurring_payment.id,
        execution_date=date(2025, 1, 15),
        status="executed",
        created_expense_id=101,
        executed_at=datetime(2025, 1, 15, 0, 1, 0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    schedule_pending = PaymentSchedule(
        id=uuid4(),
        recurring_payment_id=created_recurring_payment.id,
        execution_date=date(2025, 2, 15),
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    schedule_failed = PaymentSchedule(
        id=uuid4(),
        recurring_payment_id=created_recurring_payment.id,
        execution_date=date(2025, 3, 15),
        status="failed",
        error_message="Service unavailable",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add_all([schedule_executed, schedule_pending, schedule_failed])
    db_session.commit()
    return {
        "payment": created_recurring_payment,
        "schedules": [schedule_executed, schedule_pending, schedule_failed],
    }
