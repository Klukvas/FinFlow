import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TESTING = os.getenv("TESTING", "").lower() in ("1", "true", "yes")

# Base must be created first (used by models for table definitions)
Base = declarative_base()

# Engine and SessionLocal - only initialize if DATABASE_URL is set and NOT in test mode
# Tests will override get_db dependency with their own session and test_engine
if DATABASE_URL and not TESTING:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # Placeholder for testing - tests override get_db anyway
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Database dependency that provides a database session"""
    if SessionLocal is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL environment variable."
        )
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

