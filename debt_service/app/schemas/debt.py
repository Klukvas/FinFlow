from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

# Import contact schemas for relationships
from .contact import ContactResponse

class DebtType(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    MORTGAGE = "MORTGAGE"
    PERSONAL_LOAN = "PERSONAL_LOAN"
    AUTO_LOAN = "AUTO_LOAN"
    STUDENT_LOAN = "STUDENT_LOAN"
    OTHER = "OTHER"

class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    CHECK = "CHECK"
    AUTOMATIC = "AUTOMATIC"
    OTHER = "OTHER"

# Debt Schemas
class DebtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Debt name")
    description: Optional[str] = Field(None, description="Debt description")
    debt_type: DebtType = Field(..., description="Type of debt")
    contact_id: Optional[int] = Field(None, description="Associated contact ID")
    category_id: Optional[int] = Field(None, gt=0, description="Category ID from category service")
    
    initial_amount: float = Field(..., gt=0, description="Initial debt amount")
    interest_rate: Optional[float] = Field(None, ge=0, le=100, description="Annual interest rate (%)")
    minimum_payment: Optional[float] = Field(None, gt=0, description="Minimum payment amount")
    
    start_date: date = Field(..., description="Debt start date")
    due_date: Optional[date] = Field(None, description="Debt due date")

    @field_validator('initial_amount')
    @classmethod
    def validate_initial_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Initial amount must be greater than 0')
        return float(Decimal(str(v)).quantize(Decimal('0.01')))

    @field_validator('interest_rate')
    @classmethod
    def validate_interest_rate(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError('Interest rate must be between 0 and 100')
        return v

class DebtCreate(DebtBase):
    """Schema for creating a new debt"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Credit Card - Visa",
                "description": "Personal credit card debt",
                "debt_type": "CREDIT_CARD",
                "contact_id": 1,
                "category_id": 5,
                "initial_amount": 5000.00,
                "interest_rate": 18.99,
                "minimum_payment": 150.00,
                "start_date": "2024-01-01",
                "due_date": "2025-01-01"
            }
        }
    )

class DebtUpdate(BaseModel):
    """Schema for updating a debt"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    debt_type: Optional[DebtType] = None
    contact_id: Optional[int] = None
    category_id: Optional[int] = Field(None, gt=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    minimum_payment: Optional[float] = Field(None, gt=0)
    due_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_paid_off: Optional[bool] = None

class DebtResponse(DebtBase):
    """Schema for debt output"""
    id: int = Field(description="Unique debt identifier")
    user_id: int = Field(description="ID of the user who owns this debt")
    current_balance: float = Field(description="Current outstanding balance")
    last_payment_date: Optional[date] = Field(description="Date of last payment")
    is_active: bool = Field(description="Whether debt is active")
    is_paid_off: bool = Field(description="Whether debt is fully paid off")
    created_at: datetime
    updated_at: datetime
    
    # Include contact info if available
    contact: Optional[ContactResponse] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Credit Card - Visa",
                "debt_type": "CREDIT_CARD",
                "current_balance": 4250.00,
                "initial_amount": 5000.00,
                "interest_rate": 18.99,
                "user_id": 1,
                "is_active": True,
                "is_paid_off": False,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )

# Debt Payment Schemas
class DebtPaymentBase(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount")
    principal_amount: Optional[float] = Field(None, ge=0, description="Principal portion")
    interest_amount: Optional[float] = Field(None, ge=0, description="Interest portion")
    payment_date: date = Field(..., description="Payment date")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Payment amount must be greater than 0')
        return float(Decimal(str(v)).quantize(Decimal('0.01')))

class DebtPaymentCreate(DebtPaymentBase):
    """Schema for creating a debt payment"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 200.00,
                "principal_amount": 150.00,
                "interest_amount": 50.00,
                "payment_date": "2024-01-15",
                "description": "Monthly payment",
                "payment_method": "TRANSFER"
            }
        }
    )

class DebtPaymentResponse(DebtPaymentBase):
    """Schema for debt payment output"""
    id: int = Field(description="Unique payment identifier")
    debt_id: int = Field(description="Associated debt ID")
    user_id: int = Field(description="ID of the user who made the payment")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "debt_id": 1,
                "amount": 200.00,
                "principal_amount": 150.00,
                "interest_amount": 50.00,
                "payment_date": "2024-01-15",
                "user_id": 1,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )

# Summary and Stats Schemas
class DebtSummary(BaseModel):
    """Schema for debt summary information"""
    total_debt: float = Field(description="Total outstanding debt amount")
    total_payments: float = Field(description="Total payments made")
    active_debts: int = Field(description="Number of active debts")
    paid_off_debts: int = Field(description="Number of paid off debts")
    average_interest_rate: Optional[float] = Field(description="Average interest rate")
