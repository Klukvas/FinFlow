from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.database import Base


class SyncedTransaction(Base):
    __tablename__ = "synced_transactions"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("bank_connections.id", ondelete="CASCADE"))
    external_transaction_id = Column(String(100), nullable=False, unique=True, index=True)
    finflow_type = Column(String(10))
    finflow_id = Column(Integer)
    amount = Column(Numeric(12, 2))
    date = Column(Date)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
