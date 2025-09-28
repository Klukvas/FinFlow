from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class RecurringPaymentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название повторяющегося платежа")
    description: Optional[str] = Field(None, description="Описание платежа")
    amount: Decimal = Field(..., gt=0, description="Сумма платежа")
    currency: str = Field(default="RUB", min_length=3, max_length=3, description="Валюта")
    category_id: int = Field(..., description="ID категории")
    payment_type: str = Field(..., pattern="^(EXPENSE|INCOME)$", description="Тип платежа: EXPENSE или INCOME")
    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$", description="Тип расписания")
    schedule_config: Dict[str, Any] = Field(default_factory=dict, description="Конфигурация расписания")
    start_date: date = Field(..., description="Дата начала")
    end_date: Optional[date] = Field(None, description="Дата окончания (None = бесконечно)")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date должна быть позже start_date')
        return v

    @validator('schedule_config')
    def validate_schedule_config(cls, v, values):
        if 'schedule_type' not in values:
            return v
            
        schedule_type = values['schedule_type']
        
        if schedule_type == 'daily':
            if v:
                raise ValueError('schedule_config должен быть пустым для daily')
        elif schedule_type == 'weekly':
            if 'day_of_week' not in v or not isinstance(v['day_of_week'], int) or not (0 <= v['day_of_week'] <= 6):
                raise ValueError('schedule_config для weekly должен содержать day_of_week от 0 до 6')
        elif schedule_type == 'monthly':
            if 'day_of_month' not in v or not isinstance(v['day_of_month'], int) or not (1 <= v['day_of_month'] <= 31):
                raise ValueError('schedule_config для monthly должен содержать day_of_month от 1 до 31')
        elif schedule_type == 'yearly':
            if 'month' not in v or 'day' not in v:
                raise ValueError('schedule_config для yearly должен содержать month и day')
            if not (1 <= v['month'] <= 12) or not (1 <= v['day'] <= 31):
                raise ValueError('schedule_config для yearly: month от 1 до 12, day от 1 до 31')
                
        return v


class RecurringPaymentCreate(RecurringPaymentBase):
    pass


class RecurringPaymentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    category_id: Optional[UUID] = None
    payment_type: Optional[str] = Field(None, pattern="^(EXPENSE|INCOME)$")
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|yearly)$")
    schedule_config: Optional[Dict[str, Any]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|completed|cancelled)$")


class RecurringPaymentResponse(RecurringPaymentBase):
    id: UUID
    user_id: int
    status: str
    last_executed: Optional[datetime]
    next_execution: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecurringPaymentListResponse(BaseModel):
    items: List[RecurringPaymentResponse]
    total: int
    page: int
    size: int
    pages: int


class RecurringPaymentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|paused|completed|cancelled)$")
