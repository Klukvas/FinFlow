from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import date as datetime_date
from decimal import Decimal
import re

class ExpenseBase(BaseModel):
    amount: float = Field(
        ..., 
        gt=0, 
        le=999999.99,
        description="Expense amount (must be greater than 0 and less than 999,999.99)",
        examples=[25.50, 100.00, 1500.75]
    )
    category_id: Optional[int] = Field(
        None,
        ge=0,
        description="Optional category ID for this expense (0 means no category)",
        examples=[1, 2, 3]
    )
    account_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional account ID for this expense",
        examples=[1, 2, 3]
    )
    currency: Optional[str] = Field(
        "USD",
        max_length=3,
        min_length=3,
        description="Currency code for this expense (ISO 4217)",
        examples=["USD", "EUR", "UAH"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description of the expense",
        examples=["Lunch at restaurant", "Gas for car", "Monthly subscription"]
    )
    date: Optional[datetime_date] = Field(
        None,
        description="Date of the expense (defaults to today if not provided)",
        examples=["2024-01-15", "2024-12-25"]
    )

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate and normalize amount"""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        
        # Round to 2 decimal places
        return float(Decimal(str(v)).quantize(Decimal('0.01')))
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> str:
        """Validate currency code"""
        if v is None:
            return "USD"
        v = v.strip().upper()
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError('Currency must be a 3-letter ISO code (e.g., USD, EUR, UAH)')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description format"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 500:
                raise ValueError('Description cannot exceed 500 characters')
        return v

class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 25.50,
                "category_id": 1,
                "description": "Lunch at restaurant",
                "date": "2024-01-15"
            }
        }
    )

class ExpenseUpdate(BaseModel):
    """Schema for updating an existing expense"""
    amount: Optional[float] = Field(
        None, 
        gt=0, 
        le=999999.99,
        description="New expense amount"
    )
    category_id: Optional[int] = Field(
        None, 
        ge=0,
        description="New category ID (0 means no category)"
    )
    account_id: Optional[int] = Field(
        None,
        gt=0,
        description="New account ID"
    )
    currency: Optional[str] = Field(
        None,
        max_length=3,
        min_length=3,
        description="New currency code (ISO 4217)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="New description"
    )
    date: Optional[datetime_date] = Field(
        None,
        description="New expense date"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        """Validate and normalize amount"""
        if v is not None:
            if v <= 0:
                raise ValueError('Amount must be greater than 0')
            return float(Decimal(str(v)).quantize(Decimal('0.01')))
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code"""
        if v is not None:
            v = v.strip().upper()
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError('Currency must be a 3-letter ISO code (e.g., USD, EUR, UAH)')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description format"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 500:
                raise ValueError('Description cannot exceed 500 characters')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 30.00,
                "description": "Updated lunch description"
            }
        }
    )

class ExpenseResponse(ExpenseBase):
    """Schema for expense output with all fields"""
    id: int = Field(description="Unique expense identifier", examples=[1, 2, 3])
    user_id: int = Field(description="ID of the user who owns this expense", examples=[1, 2, 3])
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "amount": 25.50,
                "category_id": 1,
                "account_id": 1,
                "description": "Lunch at restaurant",
                "date": "2024-01-15",
                "user_id": 1
            }
        }
    )

class ExpenseSummary(BaseModel):
    """Simplified expense schema for summaries and lists"""
    id: int
    amount: float
    category_id: int
    account_id: Optional[int]
    description: Optional[str]
    date: datetime_date

    model_config = ConfigDict(from_attributes=True)

class ExpenseStats(BaseModel):
    """Schema for expense statistics"""
    total_amount: float = Field(description="Total amount of expenses")
    count: int = Field(description="Number of expenses")
    average_amount: float = Field(description="Average expense amount")
    category_breakdown: dict = Field(description="Breakdown by category")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_amount": 1250.75,
                "count": 15,
                "average_amount": 83.38,
                "category_breakdown": {
                    "1": {"name": "Food", "amount": 500.25, "count": 8},
                    "2": {"name": "Transport", "amount": 750.50, "count": 7}
                }
            }
        }
    )

class ExpenseListResponse(BaseModel):
    """Paginated response schema for expenses"""
    items: List[ExpenseResponse] = Field(description="List of expenses")
    total: int = Field(description="Total number of expenses")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "amount": 25.50,
                        "category_id": 1,
                        "account_id": 1,
                        "description": "Lunch at restaurant",
                        "date": "2024-01-15",
                        "user_id": 1,
                        "currency": "USD"
                    }
                ],
                "total": 150,
                "page": 1,
                "size": 10,
                "pages": 15
            }
        }
    )