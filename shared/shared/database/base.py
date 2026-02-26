"""
Shared database utilities — engine, session factory, Base, and get_db dependency.

Replaces boilerplate in 12+ per-service app/database.py files.

Usage in each service's database.py:
    from shared.database import create_engine_factory, create_session_factory, Base, get_db_dependency
    from app.config import settings

    engine = create_engine_factory(settings.DATABASE_URL, echo=settings.DEBUG)
    SessionLocal = create_session_factory(engine)

    get_db = get_db_dependency(SessionLocal)
"""

from typing import Generator, Callable

from sqlalchemy import create_engine as sa_create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all service models."""
    pass


def create_engine_factory(
    database_url: str,
    echo: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 300,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> Engine:
    """Create a SQLAlchemy engine with sensible defaults."""
    return sa_create_engine(
        database_url,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
    )


def create_session_factory(engine: Engine) -> sessionmaker:
    """Create a session factory bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_dependency(session_factory: sessionmaker) -> Callable[[], Generator[Session, None, None]]:
    """
    Create a FastAPI-compatible get_db dependency.

    Returns a function that yields a database session and handles cleanup.
    """
    def get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return get_db
