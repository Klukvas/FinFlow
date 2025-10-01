from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.account import AccountType

class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    type: AccountType = Field(..., description="Account type")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (ISO 4217)")
    balance: float = Field(default=0.0, ge=-999999999.99, le=999999999.99, description="Account balance")
    description: Optional[str] = Field(None, max_length=500, description="Account description")
    
    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency must be a 3-letter ISO code')
        return v.upper() if v else v

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[AccountType] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    balance: Optional[float] = Field(None, ge=-999999999.99, le=999999999.99)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency must be a 3-letter ISO code')
        return v.upper() if v else v

class AccountResponse(AccountBase):
    id: int
    owner_id: int
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AccountSummary(BaseModel):
    id: int
    name: str
    type: AccountType
    currency: str
    balance: float
    is_active: bool
    transaction_count: int = 0
    last_transaction_date: Optional[datetime] = None

class AccountTransaction(BaseModel):
    id: int
    amount: float
    description: Optional[str]
    date: datetime
    type: str  # "expense" or "income"
    category_id: Optional[int] = None
    category_name: Optional[str] = None

class AccountTransactionSummary(BaseModel):
    account: AccountSummary
    transactions: list[AccountTransaction]
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_change: float = 0.0
