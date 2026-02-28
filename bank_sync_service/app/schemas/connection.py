from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConnectionCreate(BaseModel):
    token: str = Field(
        ..., min_length=1, max_length=512, description="Monobank personal API token"
    )


class LinkedAccountResponse(BaseModel):
    id: int
    external_account_id: str
    account_name: Optional[str] = None
    currency: Optional[str] = None
    currency_code: Optional[int] = None
    masked_pan: Optional[str] = None
    iban: Optional[str] = None
    finflow_account_id: Optional[int] = None
    is_synced: bool = True

    class Config:
        from_attributes = True


class ConnectionResponse(BaseModel):
    id: int
    bank_type: str
    client_name: Optional[str] = None
    is_active: bool
    last_sync_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    accounts: list[LinkedAccountResponse] = []

    class Config:
        from_attributes = True


class LinkAccountRequest(BaseModel):
    finflow_account_id: int
