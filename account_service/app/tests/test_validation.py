"""
Tests for app/utils/validation.py — input validation functions.
"""
import pytest

from app.utils.validation import (
    validate_currency_code,
    validate_balance,
    validate_account_name,
    validate_account_description,
    sanitize_input,
)


class TestValidateCurrencyCode:
    def test_valid_code_usd(self):
        assert validate_currency_code("USD") is True

    def test_valid_code_eur(self):
        assert validate_currency_code("EUR") is True

    def test_valid_code_gbp(self):
        assert validate_currency_code("GBP") is True

    def test_lowercase_rejected(self):
        assert validate_currency_code("usd") is False

    def test_mixed_case_rejected(self):
        assert validate_currency_code("Usd") is False

    def test_too_short(self):
        assert validate_currency_code("US") is False

    def test_too_long(self):
        assert validate_currency_code("USDD") is False

    def test_empty_string(self):
        assert validate_currency_code("") is False

    def test_numeric_string(self):
        assert validate_currency_code("123") is False

    def test_alphanumeric(self):
        assert validate_currency_code("U1D") is False

    def test_none_like_empty(self):
        # The function checks `not currency` first — empty string triggers it
        assert validate_currency_code("") is False

    def test_special_characters(self):
        assert validate_currency_code("US$") is False


class TestValidateBalance:
    def test_zero(self):
        assert validate_balance(0.0) is True

    def test_positive(self):
        assert validate_balance(1000.50) is True

    def test_negative_within_range(self):
        assert validate_balance(-500.0) is True

    def test_max_boundary(self):
        assert validate_balance(999999999.99) is True

    def test_min_boundary(self):
        assert validate_balance(-999999999.99) is True

    def test_exceeds_max(self):
        assert validate_balance(999999999.999) is False

    def test_below_min(self):
        assert validate_balance(-1000000000.0) is False

    def test_large_positive(self):
        assert validate_balance(5000000000.0) is False


class TestValidateAccountName:
    def test_valid_name(self):
        assert validate_account_name("My Savings") is True

    def test_single_char(self):
        assert validate_account_name("A") is True

    def test_max_length(self):
        assert validate_account_name("A" * 100) is True

    def test_exceeds_max_length(self):
        assert validate_account_name("A" * 101) is False

    def test_empty_string(self):
        assert validate_account_name("") is False

    def test_whitespace_only(self):
        assert validate_account_name("   ") is False

    def test_name_with_leading_trailing_spaces(self):
        # Stripped length is within bounds
        assert validate_account_name("  Valid Name  ") is True

    def test_none_rejected(self):
        # `not None` is True, so it would fail early
        assert validate_account_name(None) is False


class TestValidateAccountDescription:
    def test_none_is_valid(self):
        assert validate_account_description(None) is True

    def test_empty_string(self):
        assert validate_account_description("") is True

    def test_valid_description(self):
        assert validate_account_description("A savings account for emergencies") is True

    def test_max_length(self):
        assert validate_account_description("A" * 500) is True

    def test_exceeds_max_length(self):
        assert validate_account_description("A" * 501) is False


class TestSanitizeInput:
    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_no_change_needed(self):
        assert sanitize_input("clean") == "clean"

    def test_empty_string(self):
        assert sanitize_input("") == ""

    def test_none_returns_none(self):
        assert sanitize_input(None) is None

    def test_only_whitespace(self):
        assert sanitize_input("   ") == ""

    def test_tabs_and_newlines(self):
        assert sanitize_input("\t\nhello\t\n") == "hello"
