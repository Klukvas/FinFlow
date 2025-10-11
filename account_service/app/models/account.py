from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class AccountType(str, enum.Enum):
    CASH = "cash"
    BANK = "bank"
    CRYPTO = "crypto"
    INVESTMENT = "investment"
    CREDIT = "credit"
    SAVINGS = "savings"
    CHECKING = "checking"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    balance = Column(Float, nullable=False, default=0.0)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # User ownership
    owner_id = Column(Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}', balance={self.balance})>"
