"""
Bank-specific header indicators for statement parsing
"""

from typing import Dict, List

# Header indicators for bank statements
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
    },
    "PRIVATBANK": {
        "ua": [
            "дата",
            "категорія",
            "картка",
            "опис операції",
            "сума в валюті картки"
        ],
        "en": [
            "date",
            "category",
            "card",
            "operation description",
            "amount"
        ]
    },
    "UKRSIBBANK": {
        "ua": [
            "дата операції",
            "дата розрахунку",
            "опис операції",
            "код авторизації",
            "сума в валюті рахунку"
        ],
        "en": [
            "operation date",
            "settlement date",
            "operation description",
            "authorization code",
            "amount in account currency"
        ]
    },
    "ABANK": {
        "ua": [
            "дата і час операції",
            "номер картки",
            "деталі операції",
            "мсс",
            "сума у валюті карти",
            "залишок після операції"
        ],
        "en": [
            "date and time",
            "card number",
            "operation details",
            "mcc",
            "amount in card currency",
            "balance after"
        ]
    },
    "DEEL": {
        "en": [
            "date requested",
            "transaction status",
            "transaction type",
            "currency",
            "transaction amount",
            "client",
            "withdraw method"
        ]
    }
}

# Transaction patterns by bank
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
    },
    "PRIVATBANK": {
        "income": [
            "зарахування",
            "поповнення",
            "повернення"
        ],
        "expense": [
            "оплата",
            "перекази",
            "зняття готівки",
            "комісія"
        ]
    },
    "UKRSIBBANK": {
        "income": [
            "зарахування",
            "поповнення",
            "повернення"
        ],
        "expense": [
            "комісія",
            "переказ",
            "перерахування",
            "оплата",
            "отримання готівки",
            "списання"
        ]
    },
    "ABANK": {
        "income": [
            "зарахування",
            "поповнення",
            "валютообмін"
        ],
        "expense": [
            "переказ",
            "оплата",
            "зняття"
        ]
    },
    "DEEL": {
        "income": [
            "client_payment"
        ],
        "expense": [
            "withdrawal"
        ]
    }
}

def get_headers_for_bank(bank_name: str, language: str = "ua") -> List[str]:
    """Get header indicators for a bank and language"""
    bank_key = bank_name.upper()
    return BANK_HEADERS.get(bank_key, {}).get(language, [])

def get_patterns_for_bank(bank_name: str) -> Dict[str, List[str]]:
    """Get transaction patterns for a bank"""
    bank_key = bank_name.upper()
    return TRANSACTION_PATTERNS.get(bank_key, {"income": [], "expense": []})

def get_all_headers_for_bank(bank_name: str) -> List[str]:
    """Get all header indicators for a bank (both languages)"""
    bank_key = bank_name.upper()
    bank_headers = BANK_HEADERS.get(bank_key, {})
    all_headers = []
    for lang_headers in bank_headers.values():
        all_headers.extend(lang_headers)
    return all_headers

def get_all_patterns_for_bank(bank_name: str) -> List[str]:
    """Get all transaction patterns for a bank (both income and expense)"""
    bank_key = bank_name.upper()
    bank_patterns = TRANSACTION_PATTERNS.get(bank_key, {})
    all_patterns = []
    for pattern_list in bank_patterns.values():
        all_patterns.extend(pattern_list)
    return all_patterns
