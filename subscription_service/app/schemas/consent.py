"""
Consent schemas for API requests and responses
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, validator


class ConsentRecordRequest(BaseModel):
    """Request to record user consent"""
    subscription_id: int = Field(..., description="Subscription ID")
    consent_version: str = Field(..., description="Consent version", min_length=1, max_length=16)
    consent_language: str = Field(..., description="Language code (en, uk)", min_length=2, max_length=8)
    plan_name: str = Field(..., description="Plan name", min_length=1)
    plan_code: str = Field(..., description="Plan code", min_length=1)
    amount: str = Field(..., description="Subscription amount")
    currency: str = Field(..., description="Currency code", min_length=3, max_length=3)
    browser_fingerprint: str | None = Field(None, description="Optional browser fingerprint")
    
    @validator('consent_language')
    def validate_language(cls, v):
        allowed_languages = ['en', 'uk', 'ru']
        if v not in allowed_languages:
            raise ValueError(f"Language must be one of: {', '.join(allowed_languages)}")
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        return v.upper()


class ConsentRecordResponse(BaseModel):
    """Response after recording consent"""
    id: int
    subscription_id: int
    user_id: str
    consent_version: str
    consent_language: str
    consent_given_at: datetime
    ip_address: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConsentHistoryResponse(BaseModel):
    """User's consent history"""
    id: int
    subscription_id: int
    consent_version: str
    consent_text: str
    consent_language: str
    consent_given_at: datetime
    ip_address: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConsentVersionResponse(BaseModel):
    """Current consent version information"""
    version: str
    supported_languages: list[str]
