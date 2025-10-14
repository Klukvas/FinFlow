from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class CurrencyInfo(BaseModel):
    """Information about a currency"""
    code: str = Field(..., description="Currency code (e.g., USD, EUR)")
    name: str = Field(..., description="Currency name (e.g., US Dollar)")
    symbol: str = Field(..., description="Currency symbol (e.g., $, €)")
    flag: str = Field(..., description="Country flag emoji")
    locale: str = Field(..., description="Locale for formatting (e.g., en-US, de-DE)")

class ExchangeRate(BaseModel):
    """Exchange rate information"""
    from_currency: str = Field(..., description="Source currency code")
    to_currency: str = Field(..., description="Target currency code")
    rate: float = Field(..., description="Exchange rate")
    timestamp: datetime = Field(..., description="Rate timestamp")

class ConversionRequest(BaseModel):
    """Request for currency conversion"""
    amount: float = Field(..., description="Amount to convert (can be negative)")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")

class ConversionResponse(BaseModel):
    """Response for currency conversion"""
    amount: float = Field(..., description="Original amount")
    converted_amount: float = Field(..., description="Converted amount")
    from_currency: str = Field(..., description="Source currency code")
    to_currency: str = Field(..., description="Target currency code")
    rate: float = Field(..., description="Exchange rate used")
    timestamp: datetime = Field(..., description="Conversion timestamp")

class CurrencyRatesResponse(BaseModel):
    """Response for currency rates"""
    base_currency: str = Field(..., description="Base currency")
    rates: Dict[str, float] = Field(..., description="Exchange rates")
    timestamp: datetime = Field(..., description="Rates timestamp")

class SupportedCurrenciesResponse(BaseModel):
    """Response for supported currencies"""
    currencies: List[CurrencyInfo] = Field(..., description="List of supported currencies")
    total_count: int = Field(..., description="Total number of supported currencies")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    redis_connected: bool = Field(..., description="Redis connection status")
    api_accessible: bool = Field(..., description="External API accessibility")
