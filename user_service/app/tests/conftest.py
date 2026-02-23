import os
import sys

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token")

# Add logging directory to path (resolves logging_utils import in Docker/local)
_logging_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logging")
sys.path.insert(0, os.path.abspath(_logging_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

from app.main import app
from app.database import Base
from app.dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

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

app.dependency_overrides[get_db] = override_get_db


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
        "password": fake.password()
    }