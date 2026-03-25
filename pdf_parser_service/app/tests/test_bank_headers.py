"""
Tests for bank_headers configuration module.

Covers:
- BANK_HEADERS structure
- TRANSACTION_PATTERNS structure
- get_headers_for_bank: language-specific header lookup
- get_patterns_for_bank: pattern lookup
- get_all_headers_for_bank: combined headers
- get_all_patterns_for_bank: combined patterns
"""

import pytest

from app.config.bank_headers import (
    BANK_HEADERS,
    TRANSACTION_PATTERNS,
    get_headers_for_bank,
    get_patterns_for_bank,
    get_all_headers_for_bank,
    get_all_patterns_for_bank,
)


class TestBankHeaders:

    def test_all_expected_banks_present(self):
        expected = {"MONOBANK", "PRIVATBANK", "UKRSIBBANK", "ABANK", "DEEL"}
        assert expected.issubset(set(BANK_HEADERS.keys()))

    def test_monobank_has_ua_and_en(self):
        assert "ua" in BANK_HEADERS["MONOBANK"]
        assert "en" in BANK_HEADERS["MONOBANK"]

    def test_deel_has_only_english(self):
        assert "en" in BANK_HEADERS["DEEL"]
        assert "ua" not in BANK_HEADERS["DEEL"]

    def test_headers_are_non_empty_lists(self):
        for bank, langs in BANK_HEADERS.items():
            for lang, headers in langs.items():
                assert isinstance(headers, list), f"{bank}/{lang} not a list"
                assert len(headers) > 0, f"{bank}/{lang} is empty"


class TestTransactionPatterns:

    def test_all_expected_banks_present(self):
        expected = {"MONOBANK", "PRIVATBANK", "UKRSIBBANK", "ABANK", "DEEL"}
        assert expected.issubset(set(TRANSACTION_PATTERNS.keys()))

    def test_each_bank_has_income_and_expense(self):
        for bank, patterns in TRANSACTION_PATTERNS.items():
            assert "income" in patterns, f"{bank} missing income patterns"
            assert "expense" in patterns, f"{bank} missing expense patterns"

    def test_patterns_are_non_empty(self):
        for bank, patterns in TRANSACTION_PATTERNS.items():
            for category, words in patterns.items():
                assert len(words) > 0, f"{bank}/{category} has no patterns"


class TestGetHeadersForBank:

    def test_monobank_ua(self):
        headers = get_headers_for_bank("monobank", "ua")
        assert len(headers) > 0
        assert any("операції" in h for h in headers)

    def test_monobank_en(self):
        headers = get_headers_for_bank("monobank", "en")
        assert len(headers) > 0

    def test_case_insensitive(self):
        result_lower = get_headers_for_bank("monobank", "ua")
        result_upper = get_headers_for_bank("MONOBANK", "ua")
        assert result_lower == result_upper

    def test_nonexistent_bank_returns_empty(self):
        assert get_headers_for_bank("fakebank", "ua") == []

    def test_nonexistent_language_returns_empty(self):
        assert get_headers_for_bank("monobank", "de") == []


class TestGetPatternsForBank:

    def test_monobank_patterns(self):
        patterns = get_patterns_for_bank("monobank")
        assert "income" in patterns
        assert "expense" in patterns

    def test_nonexistent_bank_returns_defaults(self):
        patterns = get_patterns_for_bank("fakebank")
        assert patterns == {"income": [], "expense": []}

    def test_case_insensitive(self):
        result_lower = get_patterns_for_bank("privatbank")
        result_upper = get_patterns_for_bank("PRIVATBANK")
        assert result_lower == result_upper


class TestGetAllHeadersForBank:

    def test_combines_all_languages(self):
        headers = get_all_headers_for_bank("monobank")
        # Should have headers from both ua and en
        assert len(headers) > len(get_headers_for_bank("monobank", "ua"))

    def test_nonexistent_bank_returns_empty(self):
        assert get_all_headers_for_bank("fakebank") == []


class TestGetAllPatternsForBank:

    def test_combines_income_and_expense(self):
        patterns = get_all_patterns_for_bank("monobank")
        income_patterns = TRANSACTION_PATTERNS["MONOBANK"]["income"]
        expense_patterns = TRANSACTION_PATTERNS["MONOBANK"]["expense"]
        assert len(patterns) == len(income_patterns) + len(expense_patterns)

    def test_nonexistent_bank_returns_empty(self):
        assert get_all_patterns_for_bank("fakebank") == []
