from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class CategoryType(enum.Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    type = Column(Enum(CategoryType), nullable=False, default=CategoryType.EXPENSE)

    # Self-referential relationship for parent-child categories
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")