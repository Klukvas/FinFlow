from fastapi import Depends
from app.services.currency import CurrencyService

def get_currency_service() -> CurrencyService:
    """Get currency service instance"""
    return CurrencyService()
