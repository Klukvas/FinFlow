import os
import sys
from uuid import UUID
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from cryptography.fernet import Fernet

# Generate a valid Fernet key for tests
_TEST_FERNET_KEY = Fernet.generate_key().decode()

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-bank-sync")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")
os.environ.setdefault("BANK_TOKEN_ENCRYPTION_KEY", _TEST_FERNET_KEY)
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://workspace-service")
os.environ.setdefault("EXPENSE_SERVICE_URL", "http://expense-service")
os.environ.setdefault("INCOME_SERVICE_URL", "http://income-service")
os.environ.setdefault("ACCOUNT_SERVICE_URL", "http://account-service")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://category-service")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://subscription-service")
os.environ.setdefault("MONOBANK_API_BASE_URL", "https://api.monobank.ua")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db
from shared.auth.dependencies import get_current_user_id, get_workspace_id

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_ID_HEADER = str(TEST_WORKSPACE_ID)
INTERNAL_TOKEN = "test-internal-token"
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_TOKEN}

# Shared connection so all sessions see the same data
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_connection = engine.connect()
Base.metadata.create_all(bind=_connection)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=_connection
)


def override_get_current_user_id():
    return TEST_USER_ID


def override_get_workspace_id():
    return TEST_WORKSPACE_ID


app.dependency_overrides[get_current_user_id] = override_get_current_user_id
app.dependency_overrides[get_workspace_id] = override_get_workspace_id


@pytest.fixture(autouse=True)
def mock_workspace_authorize():
    """Automatically mock workspace authorization for all tests."""
    with patch(
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner"),
    ), patch(
        "shared.clients.workspace.WorkspaceClient.get_instance",
        return_value=MagicMock(authorize=MagicMock(return_value=(True, "owner"))),
    ):
        yield


@pytest.fixture
def db():
    """Provide a shared test database session."""
    session = TestingSessionLocal()

    def override_get_db_shared():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db_shared
    try:
        yield session
    finally:
        # Clean up all data after each test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
        app.dependency_overrides[get_db] = _default_override_get_db


def _default_override_get_db():
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


app.dependency_overrides[get_db] = _default_override_get_db


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Return headers with Authorization and X-Workspace-Id."""
    return {
        "Authorization": "Bearer test-token",
        "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
    }


@pytest.fixture
def fernet_key():
    """Return the test Fernet key."""
    return _TEST_FERNET_KEY
