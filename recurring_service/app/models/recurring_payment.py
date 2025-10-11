from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Date, Text, JSON, Enum, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.database import Base


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    category_id = Column(Integer, nullable=False)
    payment_type = Column(Enum("EXPENSE", "INCOME", name="payment_type_enum"), nullable=False)
    schedule_type = Column(Enum("daily", "weekly", "monthly", "yearly", name="schedule_type_enum"), nullable=False)
    schedule_config = Column(JSON, nullable=False, default=dict)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(Enum("active", "paused", "completed", "cancelled", name="status_enum"), nullable=False, default="active")
    last_executed = Column(DateTime, nullable=True)
    next_execution = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment_schedules = relationship("PaymentSchedule", back_populates="recurring_payment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RecurringPayment(id={self.id}, name='{self.name}', type='{self.payment_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "amount": float(self.amount),
            "currency": self.currency,
            "category_id": self.category_id,
            "payment_type": self.payment_type,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "next_execution": self.next_execution.isoformat() if self.next_execution else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
