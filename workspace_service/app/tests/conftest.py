"""
Test configuration and fixtures for workspace service tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user_id, verify_internal_token


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    """Override user authentication for testing"""
    return 1


def override_verify_internal_token():
    """Override internal token verification for testing"""
    return None


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden dependencies"""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[verify_internal_token] = override_verify_internal_token
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return authorization headers for testing"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def internal_headers():
    """Return internal service headers for testing"""
    return {"Authorization": "Bearer my-secret-token"}

