import os
import sys

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("ACCOUNT_SERVICE_URL", "http://localhost:8009")

# Add logging directory to path (resolves logging_utils import)
_logging_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logging")
sys.path.insert(0, os.path.abspath(_logging_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker
from unittest.mock import patch
from uuid import UUID

from app.main import app
from app.database import Base
from app.dependencies import get_db, get_workspace_id, get_current_user_id

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}

# не просто engine, а сохраняем connection
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
connection = engine.connect()
Base.metadata.create_all(bind=connection)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)


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


@pytest.fixture(autouse=True)
def mock_workspace_authorize():
    """Auto-mock workspace authorization so all tests pass workspace checks."""
    with patch(
        "app.services.workspace_authorization.WorkspaceClient.authorize",
        return_value=(True, "owner")
    ):
        yield


@pytest.fixture(autouse=True)
def mock_subscription_check():
    """Auto-mock subscription check so expense creation is not blocked."""
    with patch(
        "app.clients.subscription.SubscriptionClient.check_expense_limit",
        return_value=True
    ):
        yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def fake():
    return Faker()

@pytest.fixture
def user_data(fake):
    return {
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password()
    }
