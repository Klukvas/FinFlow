from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class CategoryType(enum.Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class CategoryCreatedBy(enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    type = Column(Enum(CategoryType), nullable=False, default=CategoryType.EXPENSE)
    
    # MCC-related fields
    mcc_code = Column(Integer, ForeignKey("mcc_codes.mcc_code"), nullable=True)
    created_by = Column(Enum(CategoryCreatedBy), nullable=False, default=CategoryCreatedBy.USER)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Self-referential relationship for parent-child categories
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")