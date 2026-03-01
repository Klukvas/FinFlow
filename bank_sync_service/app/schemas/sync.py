from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class SyncRequest(BaseModel):
    account_ids: Optional[list[int]] = None
    days_back: int = Field(default=30, ge=1, le=30)


class SyncPreviewRequest(BaseModel):
    account_ids: Optional[list[int]] = None
    days_back: int = Field(default=30, ge=1, le=30)


class SyncPreviewTransaction(BaseModel):
    external_id: str
    type: str
    amount: Decimal
    currency: str
    date: date
    description: str
    mcc: Optional[int] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    account_id: int


class SyncPreviewResponse(BaseModel):
    transactions: list[SyncPreviewTransaction]
    total_found: int
    total_new: int
    total_skipped: int


class SyncConfirmTransaction(BaseModel):
    external_id: str
    type: str
    amount: Decimal
    currency: str
    date: date
    description: str
    category_id: Optional[int] = None
    account_id: int


class SyncConfirmRequest(BaseModel):
    days_back: int = Field(default=30, ge=1, le=30)
    transactions: list[SyncConfirmTransaction]


class SyncStatusResponse(BaseModel):
    id: int
    status: str
    transactions_found: int = 0
    transactions_imported: int = 0
    transactions_skipped: int = 0
    error_message: Optional[str] = None
    sync_from: Optional[datetime] = None
    sync_to: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncedTransactionResponse(BaseModel):
    external_id: str
    type: str
    amount: Decimal
    currency: Optional[str] = None
    date: date
    description: Optional[str] = None
    mcc: Optional[int] = None
    category_name: Optional[str] = None
