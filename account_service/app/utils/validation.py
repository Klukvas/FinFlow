from typing import Optional
from app.exceptions import AccountValidationError

def validate_currency_code(currency: str) -> bool:
    """Validate currency code format"""
    if not currency or len(currency) != 3:
        return False
    return currency.isalpha() and currency.isupper()

def validate_balance(balance: float) -> bool:
    """Validate account balance"""
    return -999999999.99 <= balance <= 999999999.99

def validate_account_name(name: str) -> bool:
    """Validate account name"""
    if not name or len(name.strip()) == 0:
        return False
    return len(name.strip()) <= 100

def validate_account_description(description: Optional[str]) -> bool:
    """Validate account description"""
    if description is None:
        return True
    return len(description) <= 500

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return text
    return text.strip()
