from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date

class IncomeBase(BaseModel):
    amount: float = Field(..., gt=0, description="Income amount (must be greater than 0)")
    category_id: Optional[int] = Field(None, description="Category ID for this income")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    date: Optional[str] = Field(None, description="Income date (defaults to today if not provided)")

class IncomeCreate(IncomeBase):
    """Schema for creating a new income"""
    pass

class IncomeUpdate(BaseModel):
    """Schema for updating an existing income"""
    amount: Optional[float] = Field(None, gt=0, description="New income amount")
    category_id: Optional[int] = Field(None, description="New category ID")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    date: Optional[str] = Field(None, description="New income date")

class IncomeOut(IncomeBase):
    """Schema for income output"""
    id: int
    user_id: int
    date: datetime  # Override the string type from IncomeBase to datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class IncomeSummary(BaseModel):
    """Schema for income summary statistics"""
    total_income: float
    count: int
    average_income: float
    period_start: date
    period_end: date

class IncomeStats(BaseModel):
    """Schema for income statistics"""
    total_income: float
    monthly_income: float
    yearly_income: float
    income_count: int
    average_income: float
