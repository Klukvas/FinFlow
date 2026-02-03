"""
Database configuration for PDF Parser Service.

This module sets up SQLAlchemy engine, session, and base model
for tracking PDF upload history and enforcing usage limits.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.config import settings

# Create engine from settings
engine = create_engine(settings.database_url)

# Session factory for database connections
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency injection for FastAPI.

    Yields a database session that is automatically closed after use.

    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            # use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
