from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, server_default=func.now())
    description = Column(String, nullable=True)

    user_id = Column(Integer, index=True)  # внешний ключ логически
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(Integer, nullable=True)
    account_id = Column(Integer, nullable=True, index=True)  # Optional account reference
    currency = Column(String(3), nullable=False, default="USD")  # Currency code
    
    # Add composite indexes for workspace queries
    __table_args__ = (
        Index('idx_expenses_workspace_user', 'workspace_id', 'user_id'),
        Index('idx_expenses_workspace_date', 'workspace_id', 'date'),
    )