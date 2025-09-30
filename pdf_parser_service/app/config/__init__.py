"""
Configuration package for PDF parser service
"""

from .bank_headers import (
    BANK_HEADERS,
    TRANSACTION_PATTERNS,
    get_headers_for_bank,
    get_patterns_for_bank,
    get_all_headers_for_bank,
    get_all_patterns_for_bank
)

from .config import settings

__all__ = [
    "BANK_HEADERS",
    "TRANSACTION_PATTERNS", 
    "get_headers_for_bank",
    "get_patterns_for_bank",
    "get_all_headers_for_bank",
    "get_all_patterns_for_bank",
    "settings"
]
