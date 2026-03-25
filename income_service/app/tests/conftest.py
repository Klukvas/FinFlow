"""
Shared test fixtures for income_service tests.

Sets environment variables before any app imports, configures an in-memory
SQLite database, overrides FastAPI dependencies, and auto-mocks workspace
authorization and subscription checks.
"""
import os

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-income-service")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token-income")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("ACCOUNT_SERVICE_URL", "http://localhost:8009")
os.environ.setdefault("CURRENCY_SERVICE_URL", "http://localhost:8010")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from random import randint
from uuid import UUID

from faker import Faker
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.database import Base, get_db
from app.models.income import Income
from shared.auth.dependencies import get_workspace_id

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
TEST_USER_ID = 1
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

# ---------------------------------------------------------------------------
# Database setup (shared connection to keep in-memory DB alive)
# ---------------------------------------------------------------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
connection = engine.connect()
Base.metadata.create_all(bind=connection)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=connection,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_workspace_id():
    return TEST_WORKSPACE_ID


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_workspace_id] = override_get_workspace_id


# ---------------------------------------------------------------------------
# Auto-use fixtures (workspace auth + subscription)
# ---------------------------------------------------------------------------
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
    """Auto-mock subscription check so income creation is not blocked."""
    with patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None),
    ):
        yield


# ---------------------------------------------------------------------------
# Common fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def db_session():
    """Raw database session for direct DB manipulation in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def auth_headers():
    """Authorization headers with a valid JWT for TEST_USER_ID."""
    token = make_token(TEST_USER_ID)
    return {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": str(TEST_WORKSPACE_ID),
    }


@pytest.fixture
def sample_income_payload():
    """Minimal valid income creation payload."""
    return {
        "amount": 1500.00,
        "category_id": 1,
        "currency": "USD",
        "description": "Test salary income",
        "date": "2025-01-15",
    }


@pytest.fixture
def sample_income_no_account():
    """Income payload without an account (simplest happy path)."""
    return {
        "amount": 500.00,
        "currency": "USD",
        "description": "Freelance work",
        "date": "2025-03-01",
    }


@pytest.fixture
def create_income_in_db(db_session):
    """Factory fixture to insert an Income row directly into the test DB."""

    def _create(
        user_id=TEST_USER_ID,
        workspace_id=TEST_WORKSPACE_ID,
        amount=100.00,
        category_id=None,
        account_id=None,
        currency="USD",
        description="Test income",
        income_date=None,
    ):
        income = Income(
            user_id=user_id,
            workspace_id=workspace_id,
            amount=amount,
            category_id=category_id,
            account_id=account_id,
            currency=currency,
            description=description,
            date=income_date or datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(income)
        db_session.commit()
        db_session.refresh(income)
        return income

    yield _create

    # Cleanup: remove all incomes after each test
    db_session.query(Income).delete()
    db_session.commit()


# ---------------------------------------------------------------------------
# Helper functions (importable by test modules)
# ---------------------------------------------------------------------------
def make_token(user_id: int, expired: bool = False) -> str:
    """Create a JWT token for testing."""
    exp = datetime.utcnow() + (
        timedelta(hours=-1) if expired else timedelta(hours=1)
    )
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def make_response(status_code: int, json_body=None, text_body=""):
    """Create a mock HTTP response object."""
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    resp.text = text_body
    return resp
