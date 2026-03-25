import os

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")
os.environ.setdefault("EXPENSE_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("INCOME_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8003")
os.environ.setdefault("CURRENCY_SERVICE_URL", "http://localhost:8004")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8006")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, String
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from uuid import UUID as PyUUID  # noqa: N811
from decimal import Decimal
from datetime import datetime

from app.main import app
from app.database import Base
from app.dependencies import get_db, get_workspace_id
from app.models.account import Account, AccountType

# Monkey-patch column types in the Account model for SQLite compatibility.
from sqlalchemy import TypeDecorator, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid as _uuid_mod


class SQLiteUUID(TypeDecorator):
    """Store UUID as a 36-char string in SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return _uuid_mod.UUID(value)
        return value


class SQLiteNumericAsFloat(TypeDecorator):
    """Return floats instead of Decimal for Numeric columns on SQLite."""
    impl = Float
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None:
            return float(value)
        return value


# Replace PostgreSQL-specific column types in the Account model
# so that SQLite can handle them.
for col in Account.__table__.columns:
    if isinstance(col.type, PG_UUID):
        col.type = SQLiteUUID()
    elif isinstance(col.type, Numeric):
        col.type = SQLiteNumericAsFloat()


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

TEST_WORKSPACE_ID = PyUUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_HEADER = {"X-Workspace-Id": str(TEST_WORKSPACE_ID)}
INTERNAL_TOKEN = "test-internal-token"
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_TOKEN}

# Create engine with shared connection for SQLite in-memory
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
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner")
    ):
        yield


@pytest.fixture(autouse=True)
def mock_subscription_check():
    """Auto-mock subscription check so account creation is not blocked."""
    with patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None)
    ):
        with patch(
            "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
            return_value=True
        ):
            with patch(
                "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                return_value=set()
            ):
                with patch(
                    "shared.clients.subscription.SubscriptionClient.get_user_features",
                    return_value={}
                ):
                    yield


@pytest.fixture(autouse=True)
def clean_tables():
    """Clean all rows from tables before each test for isolation."""
    db = TestingSessionLocal()
    try:
        db.query(Account).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """Provide a direct database session for setting up test data."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_account_data():
    """Return valid account creation payload."""
    return {
        "name": "Test Savings",
        "type": "savings",
        "currency": "USD",
        "balance": 1000.0,
        "description": "Test savings account"
    }


@pytest.fixture
def sample_account_update_data():
    """Return valid account update payload."""
    return {
        "name": "Updated Account",
        "balance": 2000.0,
        "description": "Updated description"
    }


def create_account_in_db(
    db_session,
    owner_id: int = 1,
    workspace_id: PyUUID = TEST_WORKSPACE_ID,
    name: str = "Test Account",
    account_type: AccountType = AccountType.SAVINGS,
    currency: str = "USD",
    balance: float = 1000.0,
    is_active: bool = True,
    is_archived: bool = False,
    description: str = None,
) -> Account:
    """Helper to insert an account directly into the test DB."""
    account = Account(
        name=name,
        type=account_type,
        currency=currency,
        balance=balance,
        description=description,
        owner_id=owner_id,
        workspace_id=workspace_id,
        is_active=is_active,
        is_archived=is_archived,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account
