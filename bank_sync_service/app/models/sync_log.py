from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("bank_connections.id", ondelete="CASCADE"))
    linked_account_id = Column(Integer, ForeignKey("linked_accounts.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending")
    transactions_found = Column(Integer, default=0)
    transactions_imported = Column(Integer, default=0)
    transactions_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    sync_from = Column(DateTime, nullable=True)
    sync_to = Column(DateTime, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    connection = relationship("BankConnection", back_populates="sync_logs")
