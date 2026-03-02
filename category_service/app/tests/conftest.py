import os
import sys
from uuid import UUID
from unittest.mock import patch

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://workspace-service")

# Add app/ directory to path (resolves `from logging_utils import ...` in middleware)
_app_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(_app_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from faker import Faker

from app.main import app
from app.database import Base
from app.dependencies import get_db, get_workspace_id

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# TEST WORKSPACE UUID used across all tests
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_ID_HEADER = str(TEST_WORKSPACE_ID)

# Shared connection so all sessions see the same data
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
connection = engine.connect()
Base.metadata.create_all(bind=connection)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=connection
)

# Module-level shared session used by the db fixture
# This session is reused so the app's override_get_db can see its data.
_shared_session: Session = None


def override_get_workspace_id():
    return TEST_WORKSPACE_ID


app.dependency_overrides[get_workspace_id] = override_get_workspace_id


@pytest.fixture(autouse=True)
def mock_workspace_authorize():
    """Automatically mock workspace authorization for all tests."""
    with patch(
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner"),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_subscription_client():
    """Automatically mock subscription client for all tests."""
    with patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.get_user_features",
        return_value={"categories": {"limit_value": 100}},
    ):
        yield


@pytest.fixture
def db():
    """Provide a shared test database session.

    Both test code and the app (via override_get_db) will use this same
    session so that data committed in the test is immediately visible to
    the app's queries.
    """
    global _shared_session
    session = TestingSessionLocal()
    _shared_session = session

    def override_get_db_shared():
        try:
            yield session
        finally:
            pass  # session is closed in the fixture teardown

    app.dependency_overrides[get_db] = override_get_db_shared
    try:
        yield session
    finally:
        session.close()
        _shared_session = None
        # Restore the default override_get_db
        app.dependency_overrides[get_db] = _default_override_get_db


def _default_override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _default_override_get_db


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="function")
def fake():
    return Faker()


@pytest.fixture
def user_data(fake):
    return {
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(),
    }


@pytest.fixture
def workspace_headers():
    """Return headers with X-Workspace-Id for requests."""
    return {"X-Workspace-Id": TEST_WORKSPACE_ID_HEADER}
