from fastapi import Depends
from app.services.category import CategoryService
from app.services.mcc_categories import DefaultCategoryService
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.logger import get_logger
from typing import Generator
from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token, decode_token

logger = get_logger(__name__)

def get_db() -> Generator[Session, None, None]:
    """Database dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_category_service(
    db: Session = Depends(get_db)
) -> CategoryService:
    """Get category service with user authentication"""
    return CategoryService(db)

def get_default_category_service(
    db: Session = Depends(get_db)
) -> DefaultCategoryService:
    """Get default category service"""
    return DefaultCategoryService(db)

def get_category_service_internal(
    db: Session = Depends(get_db)
) -> CategoryService:
    """Get category service for internal service calls"""
    return CategoryService(db)
