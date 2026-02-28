from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("bank_connections.id", ondelete="CASCADE"), nullable=False)
    external_account_id = Column(String(100), nullable=False)
    finflow_account_id = Column(Integer, nullable=True)
    account_name = Column(String(200))
    currency_code = Column(Integer)
    currency = Column(String(3))
    masked_pan = Column(String(100), nullable=True)
    iban = Column(String(50), nullable=True)
    is_synced = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    connection = relationship("BankConnection", back_populates="linked_accounts")
