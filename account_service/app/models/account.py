from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
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
    balance = Column(Numeric(12, 2), nullable=False, default=0.0)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # User ownership and workspace
    owner_id = Column(Integer, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Add composite indexes for workspace queries
    __table_args__ = (
        Index('idx_accounts_workspace_owner', 'workspace_id', 'owner_id'),
        Index('idx_accounts_workspace_name', 'workspace_id', 'name'),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}', balance={self.balance})>"
