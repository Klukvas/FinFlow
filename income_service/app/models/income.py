from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, nullable=True)  # Optional category for income
    account_id = Column(Integer, nullable=True, index=True)  # Optional account reference
    currency = Column(String(3), nullable=False, default="USD")  # Currency code
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    # Note: We don't have direct foreign key to categories table
    # as it's in a different service, but we store category_id for reference
