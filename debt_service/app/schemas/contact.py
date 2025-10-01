from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# Contact Schemas
class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    company: Optional[str] = Field(None, max_length=255, description="Company name")
    address: Optional[str] = Field(None, description="Contact address")
    notes: Optional[str] = Field(None, description="Additional notes")

class ContactCreate(ContactBase):
    """Schema for creating a new contact"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Smith",
                "email": "john@bank.com",
                "phone": "+1-555-0123",
                "company": "First National Bank",
                "address": "123 Main St, City, State 12345",
                "notes": "Primary loan officer"
            }
        }
    )

class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactResponse(ContactBase):
    """Schema for contact output"""
    id: int = Field(description="Unique contact identifier")
    user_id: int = Field(description="ID of the user who owns this contact")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "John Smith",
                "email": "john@bank.com",
                "phone": "+1-555-0123",
                "company": "First National Bank",
                "user_id": 1,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )

class ContactSummary(BaseModel):
    """Schema for contact summary"""
    id: int
    name: str
    company: Optional[str]
    debts_count: int = Field(description="Number of associated debts")
    total_debt_amount: float = Field(description="Total debt amount with this contact")
