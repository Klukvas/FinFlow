from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Union, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class BankType(str, Enum):
    MONOBANK = "monobank"
    PRIVATBANK = "privatbank"
    UKRSIBBANK = "ukrsibbank"
    RAIFFEISEN = "raiffeisen"
    OTP = "otp"
    UNIVERSAL = "universal"

class ParsedTransaction(BaseModel):
    """Schema for a parsed transaction from PDF"""
    amount: float = Field(..., description="Transaction amount")
    description: str = Field(..., description="Transaction description")
    transaction_date: date = Field(..., description="Transaction date")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    bank_type: BankType = Field(..., description="Bank that issued the PDF")
    raw_text: Optional[str] = Field(None, description="Raw text from PDF for this transaction")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for parsing accuracy")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return float(v)

class PDFParseRequest(BaseModel):
    """Schema for PDF parsing request"""
    bank_type: Optional[BankType] = Field(None, description="Specific bank type (auto-detect if not provided)")
    user_id: int = Field(..., description="User ID for context")

class PDFParseResponse(BaseModel):
    """Schema for PDF parsing response"""
    transactions: List[ParsedTransaction] = Field(..., description="List of parsed transactions")
    bank_detected: BankType = Field(..., description="Detected bank type")
    total_transactions: int = Field(..., description="Total number of transactions found")
    successful_parses: int = Field(..., description="Number of successfully parsed transactions")
    failed_parses: int = Field(..., description="Number of failed parses")
    parsing_metadata: Optional[dict] = Field(default_factory=dict, description="Additional parsing metadata")
    
class TransactionValidation(BaseModel):
    """Schema for transaction validation/editing"""
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    amount: float = Field(..., description="Validated amount")
    description: str = Field(..., description="Validated description")
    transaction_date: date = Field(..., description="Validated date")
    transaction_type: TransactionType = Field(..., description="Validated transaction type")
    category_id: Optional[int] = Field(None, description="Selected category ID")
    is_valid: bool = Field(True, description="Whether this transaction should be created")
    
class BatchCreateRequest(BaseModel):
    """Schema for batch creating transactions"""
    transactions: List[TransactionValidation] = Field(..., description="List of validated transactions")
    user_id: int = Field(..., description="User ID")
    
class BatchCreateResponse(BaseModel):
    """Schema for batch create response"""
    created_income_count: int = Field(..., description="Number of income records created")
    created_expense_count: int = Field(..., description="Number of expense records created")
    failed_transactions: List[dict] = Field(default_factory=list, description="List of failed transactions with errors")
    success: bool = Field(..., description="Whether the batch operation was successful")
