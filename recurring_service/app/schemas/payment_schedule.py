from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentScheduleResponse(BaseModel):
    id: UUID
    recurring_payment_id: UUID
    execution_date: date
    status: str
    created_expense_id: Optional[int]
    created_income_id: Optional[int]
    error_message: Optional[str]
    executed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentScheduleListResponse(BaseModel):
    items: List[PaymentScheduleResponse]
    total: int
    page: int
    size: int
    pages: int
