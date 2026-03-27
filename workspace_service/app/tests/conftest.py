"""
Test configuration and fixtures for workspace service tests.
"""
import os
import tempfile

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
# This must happen before importing anything from app.*
# Use 'TESTING' prefix so database.py knows not to create engine
os.environ["TESTING"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8000")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


# Import Base from database (this is safe - Base is created without needing DATABASE_URL)
from app.database import Base

# Now import models (they use Base)
from app.models.workspace import Workspace, WorkspaceType
from app.models.member import WorkspaceMember, MemberRole, MemberStatus
from app.models.invite import WorkspaceInvite, InviteStatus

# Import clients for mocking
from app.clients.user import UserClient, UserInfo


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test using a temp file"""
    # Create a temporary file for SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    # Create engine for this test
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    
    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        # Remove the temp database file
        try:
            os.unlink(db_path)
        except OSError:
            pass


# ==================== FastAPI Test Client ====================

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden dependencies"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    from app.dependencies import get_current_user_id, verify_internal_token
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_current_user_id():
        return 1  # Default test user is owner
    
    def override_verify_internal_token():
        return None
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[verify_internal_token] = override_verify_internal_token
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ==================== User Fixtures ====================

@pytest.fixture
def owner_user():
    """Owner user info"""
    return UserInfo(
        id=1,
        email="owner@test.com",
        base_currency="USD",
        default_workspace_id=None
    )


@pytest.fixture
def member_user():
    """Member user info"""
    return UserInfo(
        id=2,
        email="member@test.com",
        base_currency="USD",
        default_workspace_id=None
    )


@pytest.fixture
def other_user():
    """Another user info"""
    return UserInfo(
        id=3,
        email="other@test.com",
        base_currency="USD",
        default_workspace_id=None
    )


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_user_client(owner_user, member_user, other_user):
    """Create a mock UserClient"""
    mock = Mock(spec=UserClient)
    
    users = {
        1: owner_user,
        2: member_user,
        3: other_user,
    }
    
    emails = {
        "owner@test.com": owner_user,
        "member@test.com": member_user,
        "other@test.com": other_user,
    }
    
    mock.get_user.side_effect = lambda user_id: users.get(user_id)
    mock.get_user_by_email.side_effect = lambda email: emails.get(email.lower().strip())
    mock.user_exists.side_effect = lambda user_id: user_id in users
    mock.get_users_batch.side_effect = lambda ids: {uid: users[uid] for uid in ids if uid in users}
    
    return mock


@pytest.fixture
def mock_subscription_client():
    """Create a mock SubscriptionClient"""
    mock = Mock()
    mock.check_limit.return_value = (True, None)
    mock.get_workspace_limit.return_value = 10
    return mock


# ==================== Workspace Fixtures ====================

@pytest.fixture
def shared_workspace(db_session, owner_user):
    """Create a shared workspace with owner"""
    workspace = Workspace(
        id=uuid4(),
        name="Test Workspace",
        owner_user_id=owner_user.id,
    )
    workspace.type = WorkspaceType.SHARED
    print(f"[DEBUG] after assign: workspace.type={workspace.type!r}")
    db_session.add(workspace)
    db_session.flush()
    print(f"[DEBUG] after flush: workspace.type={workspace.type!r}")

    # Add owner as member
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_user.id,
        role=MemberRole.OWNER,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(owner_member)
    db_session.commit()
    print(f"[DEBUG] after commit: workspace.type={workspace.type!r}")
    db_session.refresh(workspace)
    print(f"[DEBUG] after refresh: workspace.type={workspace.type!r}")

    # Check raw DB
    from sqlalchemy import text
    rows = db_session.execute(text("SELECT id, type, name FROM workspaces")).fetchall()
    print(f"[DEBUG] all rows: {rows}")

    return workspace


@pytest.fixture
def personal_workspace(db_session, owner_user):
    """Create a personal workspace for owner"""
    workspace = Workspace(
        id=uuid4(),
        name="Personal",
        owner_user_id=owner_user.id,
    )
    workspace.type = WorkspaceType.PERSONAL
    db_session.add(workspace)
    db_session.flush()
    
    # Add owner as member
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_user.id,
        role=MemberRole.OWNER,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(owner_member)
    db_session.commit()
    db_session.refresh(workspace)
    
    return workspace


@pytest.fixture
def archived_workspace(db_session, owner_user):
    """Create an archived workspace"""
    workspace = Workspace(
        id=uuid4(),
        name="Archived Workspace",
        owner_user_id=owner_user.id,
        archived_at=datetime.utcnow(),
    )
    workspace.type = WorkspaceType.SHARED
    db_session.add(workspace)
    db_session.flush()
    
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_user.id,
        role=MemberRole.OWNER,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(owner_member)
    db_session.commit()
    db_session.refresh(workspace)
    
    return workspace


# ==================== Member Fixtures ====================

@pytest.fixture
def workspace_with_member(db_session, shared_workspace, member_user):
    """Create a workspace with an additional member"""
    member = WorkspaceMember(
        workspace_id=shared_workspace.id,
        user_id=member_user.id,
        role=MemberRole.FULL,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(member)
    db_session.commit()
    
    return shared_workspace


@pytest.fixture
def workspace_with_read_member(db_session, shared_workspace, member_user):
    """Create a workspace with a read-only member"""
    member = WorkspaceMember(
        workspace_id=shared_workspace.id,
        user_id=member_user.id,
        role=MemberRole.READ,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(member)
    db_session.commit()
    
    return shared_workspace


@pytest.fixture
def removed_member(db_session, shared_workspace, member_user):
    """Create a removed member record"""
    member = WorkspaceMember(
        workspace_id=shared_workspace.id,
        user_id=member_user.id,
        role=MemberRole.READ,
        status=MemberStatus.REMOVED,
    )
    db_session.add(member)
    db_session.commit()
    
    return member


# ==================== Invite Fixtures ====================

@pytest.fixture
def pending_invite(db_session, shared_workspace, owner_user, member_user):
    """Create a pending invite"""
    invite = WorkspaceInvite(
        id=uuid4(),
        workspace_id=shared_workspace.id,
        inviter_user_id=owner_user.id,
        invitee_user_id=member_user.id,
        invitee_email=member_user.email,
        role=MemberRole.FULL,
        status=InviteStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(days=3),
    )
    db_session.add(invite)
    db_session.commit()
    db_session.refresh(invite)
    
    return invite


@pytest.fixture
def expired_invite(db_session, shared_workspace, owner_user, member_user):
    """Create an expired invite"""
    invite = WorkspaceInvite(
        id=uuid4(),
        workspace_id=shared_workspace.id,
        inviter_user_id=owner_user.id,
        invitee_user_id=member_user.id,
        invitee_email=member_user.email,
        role=MemberRole.READ,
        status=InviteStatus.PENDING,
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
    )
    db_session.add(invite)
    db_session.commit()
    db_session.refresh(invite)
    
    return invite


@pytest.fixture
def accepted_invite(db_session, shared_workspace, owner_user, member_user):
    """Create an accepted invite"""
    invite = WorkspaceInvite(
        id=uuid4(),
        workspace_id=shared_workspace.id,
        inviter_user_id=owner_user.id,
        invitee_user_id=member_user.id,
        invitee_email=member_user.email,
        role=MemberRole.FULL,
        status=InviteStatus.ACCEPTED,
        expires_at=datetime.utcnow() + timedelta(days=3),
        accepted_at=datetime.utcnow(),
        responded_at=datetime.utcnow(),
    )
    db_session.add(invite)
    db_session.commit()
    db_session.refresh(invite)
    
    return invite


@pytest.fixture
def rejected_invite(db_session, shared_workspace, owner_user, member_user):
    """Create a rejected invite"""
    invite = WorkspaceInvite(
        id=uuid4(),
        workspace_id=shared_workspace.id,
        inviter_user_id=owner_user.id,
        invitee_user_id=member_user.id,
        invitee_email=member_user.email,
        role=MemberRole.READ,
        status=InviteStatus.REJECTED,
        expires_at=datetime.utcnow() + timedelta(days=3),
        responded_at=datetime.utcnow(),
    )
    db_session.add(invite)
    db_session.commit()
    db_session.refresh(invite)
    
    return invite


@pytest.fixture
def canceled_invite(db_session, shared_workspace, owner_user, member_user):
    """Create a canceled invite"""
    invite = WorkspaceInvite(
        id=uuid4(),
        workspace_id=shared_workspace.id,
        inviter_user_id=owner_user.id,
        invitee_user_id=member_user.id,
        invitee_email=member_user.email,
        role=MemberRole.READ,
        status=InviteStatus.CANCELED,
        expires_at=datetime.utcnow() + timedelta(days=3),
        responded_at=datetime.utcnow(),
    )
    db_session.add(invite)
    db_session.commit()
    db_session.refresh(invite)
    
    return invite


# ==================== Service Fixtures ====================

@pytest.fixture
def invite_service(db_session, mock_user_client):
    """Create InviteService with mocked dependencies"""
    from app.services.invite import InviteService
    
    service = InviteService(db_session)
    service.user_client = mock_user_client
    return service


@pytest.fixture
def workspace_service(db_session, mock_user_client, mock_subscription_client):
    """Create WorkspaceService with mocked dependencies"""
    from app.services.workspace import WorkspaceService
    
    service = WorkspaceService(db_session)
    service.user_client = mock_user_client
    service.subscription_client = mock_subscription_client
    return service


# ==================== Helper Fixtures ====================

@pytest.fixture
def auth_headers():
    """Return authorization headers for testing"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def internal_headers():
    """Return internal service headers for testing"""
    return {"Authorization": "Bearer my-secret-token"}
