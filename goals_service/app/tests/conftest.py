"""
Test configuration and fixtures for goals service tests.
"""
import os
import tempfile

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
# This must happen before importing anything from app.*
os.environ["TESTING"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token-for-testing")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8000")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://localhost:8000")
os.environ.setdefault("CURRENCY_SERVICE_URL", "http://localhost:8000")

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID

from sqlalchemy import create_engine, event, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base
from app.models.goal import Goal, GoalType, GoalStatus, GoalPriority
from app.models.milestone import Milestone


import sqlite3


def _patch_uuid_columns_for_sqlite():
    """
    Patch PostgreSQL UUID columns so they render as CHAR(36) in SQLite.
    Must be called before create_all().
    """
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = String(36)


# Register a SQLite adapter so Python UUID objects are stored as strings
sqlite3.register_adapter(UUID, lambda u: str(u))


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test using a temp file."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    _patch_uuid_columns_for_sqlite()
    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSession()

    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


# ==================== Constants ====================
# Store workspace IDs as strings because SQLite stores UUID columns as TEXT.
# SQLAlchemy filters using Python-level comparison, so UUID('x') != 'x'.

TEST_USER_ID = 1
OTHER_USER_ID = 2
TEST_WORKSPACE_ID = str(uuid4())
OTHER_WORKSPACE_ID = str(uuid4())


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_workspace_client():
    """Create a mock WorkspaceClient that authorizes all requests."""
    mock = Mock()
    mock.authorize.return_value = (True, "member")
    return mock


@pytest.fixture
def mock_subscription_client():
    """Create a mock SubscriptionClient that allows all operations."""
    mock = Mock()
    mock.check_limit.return_value = (True, None)
    mock.check_modify_allowed.return_value = True
    mock.get_read_only_ids.return_value = set()
    mock.get_user_features.return_value = {}
    return mock


@pytest.fixture
def mock_user_client():
    """Create a mock UserServiceClient."""
    mock = Mock()
    mock.get_user_base_currency.return_value = "USD"
    return mock


@pytest.fixture
def mock_currency_client():
    """Create a mock CurrencyServiceClient."""
    mock = Mock()
    mock.convert_amount.return_value = None  # No conversion by default
    return mock


# ==================== Goal Service Fixture ====================

@pytest.fixture
def goal_service(
    db_session,
    mock_workspace_client,
    mock_subscription_client,
    mock_user_client,
    mock_currency_client,
):
    """Create GoalService with all external dependencies mocked."""
    from app.services.goal import GoalService

    service = GoalService(db_session)
    service.workspace_client = mock_workspace_client
    service.subscription_client = mock_subscription_client
    service.user_client = mock_user_client
    service.currency_client = mock_currency_client
    return service


# ==================== Goal Data Fixtures ====================

@pytest.fixture
def sample_goal(db_session):
    """Create a sample goal in the database."""
    goal = Goal(
        user_id=TEST_USER_ID,
        workspace_id=TEST_WORKSPACE_ID,
        title="Save for vacation",
        description="Trip to Japan",
        goal_type=GoalType.SAVINGS,
        priority=GoalPriority.HIGH,
        status=GoalStatus.ACTIVE,
        target_amount=Decimal("5000.00"),
        current_amount=Decimal("1500.00"),
        currency="USD",
        progress_percentage=Decimal("30.0"),
        is_milestone_based=False,
        start_date=datetime.now(timezone.utc),
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


@pytest.fixture
def completed_goal(db_session):
    """Create a completed goal in the database."""
    goal = Goal(
        user_id=TEST_USER_ID,
        workspace_id=TEST_WORKSPACE_ID,
        title="Emergency fund",
        description="Build emergency fund",
        goal_type=GoalType.EMERGENCY_FUND,
        priority=GoalPriority.CRITICAL,
        status=GoalStatus.COMPLETED,
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("10000.00"),
        currency="USD",
        progress_percentage=Decimal("100.0"),
        is_milestone_based=False,
        start_date=datetime.now(timezone.utc),
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


@pytest.fixture
def multiple_goals(db_session):
    """Create multiple goals with various statuses and types."""
    goals = [
        Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Savings goal",
            goal_type=GoalType.SAVINGS,
            priority=GoalPriority.HIGH,
            status=GoalStatus.ACTIVE,
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("2000.00"),
            currency="USD",
            progress_percentage=Decimal("40.0"),
            start_date=datetime.now(timezone.utc),
        ),
        Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Debt payoff",
            goal_type=GoalType.DEBT_PAYOFF,
            priority=GoalPriority.CRITICAL,
            status=GoalStatus.ACTIVE,
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("1000.00"),
            currency="USD",
            progress_percentage=Decimal("33.33"),
            start_date=datetime.now(timezone.utc),
        ),
        Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Investment goal",
            goal_type=GoalType.INVESTMENT,
            priority=GoalPriority.MEDIUM,
            status=GoalStatus.COMPLETED,
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("10000.00"),
            currency="USD",
            progress_percentage=Decimal("100.0"),
            start_date=datetime.now(timezone.utc),
        ),
        Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Paused goal",
            goal_type=GoalType.SAVINGS,
            priority=GoalPriority.LOW,
            status=GoalStatus.PAUSED,
            target_amount=Decimal("2000.00"),
            current_amount=Decimal("500.00"),
            currency="EUR",
            progress_percentage=Decimal("25.0"),
            start_date=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(goals)
    db_session.commit()
    for g in goals:
        db_session.refresh(g)
    return goals


@pytest.fixture
def other_user_goal(db_session):
    """Create a goal belonging to a different user."""
    goal = Goal(
        user_id=OTHER_USER_ID,
        workspace_id=OTHER_WORKSPACE_ID,
        title="Other user goal",
        goal_type=GoalType.SAVINGS,
        priority=GoalPriority.MEDIUM,
        status=GoalStatus.ACTIVE,
        target_amount=Decimal("1000.00"),
        current_amount=Decimal("0.00"),
        currency="USD",
        progress_percentage=Decimal("0.0"),
        start_date=datetime.now(timezone.utc),
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


# ==================== Milestone Fixtures ====================

@pytest.fixture
def sample_milestone(db_session, sample_goal):
    """Create a sample milestone for the sample goal."""
    milestone = Milestone(
        goal_id=sample_goal.id,
        title="First milestone",
        description="Save first $1000",
        target_amount=Decimal("1000.00"),
        current_amount=Decimal("500.00"),
        is_completed=False,
        order_index=0,
    )
    db_session.add(milestone)
    db_session.commit()
    db_session.refresh(milestone)
    return milestone


@pytest.fixture
def multiple_milestones(db_session, sample_goal):
    """Create multiple milestones for the sample goal."""
    milestones = [
        Milestone(
            goal_id=sample_goal.id,
            title="Milestone 1",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            is_completed=True,
            completed_at=datetime.now(timezone.utc),
            order_index=0,
        ),
        Milestone(
            goal_id=sample_goal.id,
            title="Milestone 2",
            target_amount=Decimal("2000.00"),
            current_amount=Decimal("500.00"),
            is_completed=False,
            order_index=1,
        ),
        Milestone(
            goal_id=sample_goal.id,
            title="Milestone 3",
            target_amount=Decimal("2000.00"),
            current_amount=Decimal("0.00"),
            is_completed=False,
            order_index=2,
        ),
    ]
    db_session.add_all(milestones)
    db_session.commit()
    for m in milestones:
        db_session.refresh(m)
    return milestones


# ==================== FastAPI Test Client ====================

@pytest.fixture(scope="function")
def client(db_session, mock_subscription_client, mock_workspace_client):
    """Create a test client with overridden dependencies."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    from app.dependencies import get_current_user_id, get_workspace_id, verify_internal_token

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

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

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return authorization headers for testing."""
    return {
        "Authorization": "Bearer test-token",
        "X-Workspace-Id": str(TEST_WORKSPACE_ID),
    }


@pytest.fixture
def internal_headers():
    """Return internal service headers for testing."""
    return {
        "X-Internal-Token": "test-internal-token-for-testing",
    }
