from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Date, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentSchedule(Base):
    __tablename__ = "payment_schedules"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    recurring_payment_id = Column(PostgresUUID(as_uuid=True), ForeignKey("recurring_payments.id"), nullable=False)
    execution_date = Column(Date, nullable=False)
    status = Column(Enum("pending", "executed", "failed", name="schedule_status_enum"), nullable=False, default="pending")
    created_expense_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    created_income_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recurring_payment = relationship("RecurringPayment", back_populates="payment_schedules")

    def __repr__(self):
        return f"<PaymentSchedule(id={self.id}, execution_date='{self.execution_date}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "recurring_payment_id": str(self.recurring_payment_id),
            "execution_date": self.execution_date.isoformat() if self.execution_date else None,
            "status": self.status,
            "created_expense_id": str(self.created_expense_id) if self.created_expense_id else None,
            "created_income_id": str(self.created_income_id) if self.created_income_id else None,
            "error_message": self.error_message,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
