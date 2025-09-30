"""
Bank-specific header indicators for PDF parsing (Monobank only)
"""

from typing import Dict, List

# Header indicators for Monobank PDFs
BANK_HEADERS = {
    "MONOBANK": {
        "ua": [
            'дата i час операції', 
            'деталі операції', 
            'mcc', 
            'сума в валюті картки (uah)', 
            'сума в валюті операції', 
            'валюта', 
            'курс', 
            'сума комісій (uah)', 
            'сума кешбеку/миль', 
            'залишок після операції'
        ],
        "en": [
            "date and time",
            "operation",
            "amount",
            "currency",
            "balance",
            "mcc",
            "commission",
            "cashback"
        ]
    }
}

# Transaction patterns for Monobank
TRANSACTION_PATTERNS = {
    "MONOBANK": {
        "income": [
            "зарахування",
            "поповнення",
            "переказ",
            "повернення",
            "дохід",
            "зарплата",
            "пенсія",
            "стипендія"
        ],
        "expense": [
            "оплата",
            "покупка",
            "зняття",
            "комісія",
            "платіж",
            "витрата",
            "покупка товарів",
            "послуги"
        ]
    }
}

def get_headers_for_bank(bank_name: str, language: str = "ua") -> List[str]:
    """Get header indicators for Monobank and language"""
    if bank_name.upper() != "MONOBANK":
        return []
    return BANK_HEADERS.get("MONOBANK", {}).get(language, [])

def get_patterns_for_bank(bank_name: str) -> Dict[str, List[str]]:
    """Get transaction patterns for Monobank"""
    if bank_name.upper() != "MONOBANK":
        return {"income": [], "expense": []}
    return TRANSACTION_PATTERNS.get("MONOBANK", {"income": [], "expense": []})

def get_all_headers_for_bank(bank_name: str) -> List[str]:
    """Get all header indicators for Monobank (both languages)"""
    if bank_name.upper() != "MONOBANK":
        return []
    bank_headers = BANK_HEADERS.get("MONOBANK", {})
    all_headers = []
    for lang_headers in bank_headers.values():
        all_headers.extend(lang_headers)
    return all_headers

def get_all_patterns_for_bank(bank_name: str) -> List[str]:
    """Get all transaction patterns for Monobank (both income and expense)"""
    if bank_name.upper() != "MONOBANK":
        return []
    bank_patterns = TRANSACTION_PATTERNS.get("MONOBANK", {})
    all_patterns = []
    for pattern_list in bank_patterns.values():
        all_patterns.extend(pattern_list)
    return all_patterns