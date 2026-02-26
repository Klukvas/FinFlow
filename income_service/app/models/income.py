from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(Integer, nullable=True)  # Optional category for income
    account_id = Column(Integer, nullable=True, index=True)  # Optional account reference
    currency = Column(String(3), nullable=False, default="USD")  # Currency code
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Add composite indexes for workspace queries
    __table_args__ = (
        Index('idx_incomes_workspace_user', 'workspace_id', 'user_id'),
        Index('idx_incomes_workspace_date', 'workspace_id', 'date'),
    )
    
    # Relationships
    # Note: We don't have direct foreign key to categories table
    # as it's in a different service, but we store category_id for reference
