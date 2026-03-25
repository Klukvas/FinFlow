"""
Tests for individual bank parsers.

Covers:
- MonobankParser: row parsing, transaction type determination, MCC lookup
- PrivatbankParser: XLSX row parsing, date/amount handling
- UkrsibBankParser: 6-col and 7-col row parsing, amount parsing
- ABankParser: 11-col row parsing, credit limit skip, amount parsing
- DeelParser: CSV row parsing, status filtering, date parsing, description building
"""

import csv
import io
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.transaction import BankType, TransactionType, ParsedTransaction
from app.services.parsers.monobank_parser import MonobankParser
from app.services.parsers.privatbank_parser import PrivatbankParser
from app.services.parsers.ukrsibbank_parser import UkrsibBankParser
from app.services.parsers.abank_parser import ABankParser
from app.services.parsers.deel_parser import DeelParser


# =========================================================================
# MonobankParser
# =========================================================================

class TestMonobankParser:

    @pytest.fixture
    def parser(self):
        p = MonobankParser()
        p.category_client = MagicMock()
        p.category_client.get_mcc_category = AsyncMock(return_value=None)
        p.category_client.get_category_by_mcc = AsyncMock(return_value=None)
        return p

    @pytest.mark.asyncio
    async def test_parse_transaction_row_success(self, parser):
        row = [
            "15.01.2025 10:30",  # date+time
            "Grocery store purchase",  # description
            "5411",  # MCC
            "-150.50",  # amount UAH
            "-150.50",  # amount op currency
            "UAH",  # currency
            "1",  # rate
            "0",  # commission
            "0",  # cashback
            "10000.00",  # balance
        ]

        result = await parser._parse_transaction_row(row, "en", 1)

        assert result is not None
        assert result.amount == 150.50
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.mcc_code == 5411
        assert result.bank_type == BankType.MONOBANK

    @pytest.mark.asyncio
    async def test_parse_transaction_row_income(self, parser):
        row = [
            "10.01.2025",
            "Salary payment",
            "",
            "5000.00",
            "5000.00",
            "UAH",
            "1",
            "0",
            "0",
            "15000.00",
        ]

        result = await parser._parse_transaction_row(row, "en", 1)

        assert result is not None
        assert result.amount == 5000.00
        assert result.transaction_type == TransactionType.INCOME

    @pytest.mark.asyncio
    async def test_parse_transaction_row_invalid_amount(self, parser):
        row = [
            "15.01.2025",
            "Some transaction",
            "5411",
            "invalid_amount",
        ]

        result = await parser._parse_transaction_row(row, "en", 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_transaction_row_too_few_columns(self, parser):
        row = ["15.01.2025", "desc", "5411"]

        result = await parser._parse_transaction_row(row, "en", 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_mcc_category_lookup_integration(self, parser):
        parser.category_client.get_mcc_category = AsyncMock(
            return_value={
                "mcc_code": 5411,
                "name": "Grocery Stores",
                "translation": "Продуктовые магазины",
            }
        )
        parser.category_client.get_category_by_mcc = AsyncMock(
            return_value={"exists": True, "category_id": 42}
        )

        row = [
            "15.01.2025",
            "Purchase",
            "5411",
            "-100.00",
            "-100.00",
            "UAH",
            "1",
            "0",
            "0",
            "5000.00",
        ]

        result = await parser._parse_transaction_row(row, "ru", 1)

        assert result.mcc_category_name == "Grocery Stores"
        assert result.mcc_category_translation == "Продуктовые магазины"
        assert result.category_exists is True
        assert result.category_id == 42

    def test_calculate_transaction_type_expense(self, parser):
        assert parser._calculate_transaction_type(-100, []) == TransactionType.EXPENSE

    def test_calculate_transaction_type_income(self, parser):
        assert parser._calculate_transaction_type(100, []) == TransactionType.INCOME

    @pytest.mark.asyncio
    async def test_extract_transactions_from_table_no_header(self, parser):
        """Table without recognizable header returns empty list."""
        table = [
            ["Random", "Data", "Here", "Now"],
            ["a", "b", "c", "d"],
        ]
        result = await parser._extract_transactions_from_table(table, "en", 1)
        assert result == []


# =========================================================================
# PrivatbankParser
# =========================================================================

class TestPrivatbankParser:

    @pytest.fixture
    def parser(self):
        return PrivatbankParser()

    def test_parse_xlsx_row_success(self, parser):
        row = (
            "15.01.2025 10:30:00",  # date
            "Продукти",  # category
            "5168****1234",  # card
            "ATB Market",  # description
            -250.50,  # amount card currency
            "UAH",  # card currency
            -250.50,  # amount tx currency
            "UAH",  # tx currency
            10000.00,  # balance
            "UAH",  # balance currency
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is not None
        assert result.amount == 250.50
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.bank_type == BankType.PRIVATBANK
        assert "[Продукти] ATB Market" in result.description

    def test_parse_xlsx_row_income(self, parser):
        row = (
            "10.01.2025 09:00:00",
            "Зарплата",
            "5168****1234",
            "Salary",
            5000.00,
            "UAH",
            5000.00,
            "UAH",
            15000.00,
            "UAH",
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is not None
        assert result.transaction_type == TransactionType.INCOME

    def test_parse_xlsx_row_no_date(self, parser):
        row = (
            "not a date",
            "Cat",
            "Card",
            "Desc",
            100.0,
            "UAH",
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is None

    def test_parse_xlsx_row_none_amount(self, parser):
        row = (
            "15.01.2025 10:00:00",
            "Cat",
            "Card",
            "Desc",
            None,
            "UAH",
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is None

    def test_parse_xlsx_row_zero_amount(self, parser):
        row = (
            "15.01.2025 10:00:00",
            "Cat",
            "Card",
            "Desc",
            0.0,
            "UAH",
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is None

    def test_parse_xlsx_row_too_few_columns(self, parser):
        row = ("15.01.2025", "Cat", "Card")

        result = parser._parse_xlsx_row(row, 3)

        assert result is None

    def test_parse_xlsx_row_description_fallback(self, parser):
        """When both category and description are empty, use fallback."""
        row = (
            "15.01.2025 10:00:00",
            "",
            "Card",
            "",
            -50.0,
            "UAH",
        )

        result = parser._parse_xlsx_row(row, 3)

        assert result is not None
        assert result.description == "PrivatBank transaction"


# =========================================================================
# UkrsibBankParser
# =========================================================================

class TestUkrsibBankParser:

    @pytest.fixture
    def parser(self):
        return UkrsibBankParser()

    def test_parse_row_7col_expense(self, parser):
        """7-column card operations row."""
        row = [
            "15.01.2025",  # date
            "16.01.2025",  # settlement date
            "AUTH123",  # auth code
            "ATB Market purchase",  # description
            "UAH",  # currency
            "-250.50",  # amount op currency
            "-250.50",  # amount UAH
        ]

        result = parser._parse_row(row)

        assert result is not None
        assert result.amount == 250.50
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.bank_type == BankType.UKRSIBBANK

    def test_parse_row_6col_income(self, parser):
        """6-column account operations row."""
        row = [
            "10.01.2025",
            "10.01.2025",
            "Salary transfer",
            "UAH",
            "5000.00",
            "5000.00",
        ]

        result = parser._parse_row(row)

        assert result is not None
        assert result.amount == 5000.00
        assert result.transaction_type == TransactionType.INCOME

    def test_parse_row_no_date(self, parser):
        row = ["Not a date", "16.01.2025", "AUTH123", "Desc", "UAH", "-100", "-100"]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_empty_amount(self, parser):
        row = [
            "15.01.2025",
            "16.01.2025",
            "AUTH123",
            "Some desc",
            "UAH",
            "",
            "",
        ]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_too_few_columns(self, parser):
        row = ["15.01.2025", "data", "more"]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_none_input(self, parser):
        assert parser._parse_row(None) is None

    def test_parse_row_empty_input(self, parser):
        assert parser._parse_row([]) is None

    def test_parse_ukrsib_amount_with_spaces(self, parser):
        assert parser._parse_ukrsib_amount("-7 605.00") == -7605.00

    def test_parse_ukrsib_amount_with_nbsp(self, parser):
        assert parser._parse_ukrsib_amount("158\xa0571.00") == 158571.00

    def test_parse_ukrsib_amount_invalid(self, parser):
        assert parser._parse_ukrsib_amount("abc") is None

    def test_clean_ukrsib_description_removes_separator(self, parser):
        raw = "Payment description\n_ _ _ _ _ _ _ _ _ _ _ _ _ _\nSome details"
        result = parser._clean_ukrsib_description(raw)
        assert "_ _" not in result
        assert "Payment description" in result
        assert "Some details" in result

    def test_clean_ukrsib_description_empty(self, parser):
        assert parser._clean_ukrsib_description(None) == ""
        assert parser._clean_ukrsib_description("") == ""

    def test_parse_row_zero_amount(self, parser):
        row = [
            "15.01.2025",
            "16.01.2025",
            "AUTH123",
            "Some desc",
            "UAH",
            "0.00",
            "0.00",
        ]

        result = parser._parse_row(row)

        assert result is None


# =========================================================================
# ABankParser
# =========================================================================

class TestABankParser:

    @pytest.fixture
    def parser(self):
        return ABankParser()

    def test_parse_row_expense(self, parser):
        row = [
            "23.12.2025\n10:33",  # date+time
            "5168****1234",  # card
            "ATB Market",  # description
            "5411",  # MCC
            "-16 130.24",  # amount UAH
            "-16 130.24",  # amount op currency
            "UAH",  # currency
            "1",  # rate
            "0",  # commission
            "10.00",  # cashback
            "50 000.00",  # balance
        ]

        result = parser._parse_row(row)

        assert result is not None
        assert result.amount == 16130.24
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.mcc_code == 5411
        assert result.bank_type == BankType.ABANK

    def test_parse_row_income(self, parser):
        row = [
            "10.01.2025",
            "5168****1234",
            "Salary",
            "",
            "50 000.00",
            "50 000.00",
            "UAH",
            "1",
            "0",
            "0",
            "100 000.00",
        ]

        result = parser._parse_row(row)

        assert result is not None
        assert result.transaction_type == TransactionType.INCOME

    def test_parse_row_skips_credit_limit(self, parser):
        row = [
            "15.01.2025",
            "5168****1234",
            "Збільшення кредитного ліміту по картці",
            "",
            "100 000.00",
            "100 000.00",
            "UAH",
            "1",
            "0",
            "0",
            "200 000.00",
        ]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_no_date(self, parser):
        row = ["header row", "card", "desc", "mcc", "100", "100", "UAH", "1", "0", "0", "500"]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_too_few_columns(self, parser):
        row = ["15.01.2025", "card", "desc"]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_row_zero_amount(self, parser):
        row = [
            "15.01.2025",
            "5168****1234",
            "Zero transaction",
            "5411",
            "0.00",
            "0.00",
            "UAH",
            "1",
            "0",
            "0",
            "50 000.00",
        ]

        result = parser._parse_row(row)

        assert result is None

    def test_parse_abank_amount_positive(self, parser):
        assert parser._parse_abank_amount("50 000.00") == 50000.00

    def test_parse_abank_amount_negative(self, parser):
        assert parser._parse_abank_amount("-16 130.24") == -16130.24

    def test_parse_abank_amount_invalid(self, parser):
        assert parser._parse_abank_amount("not a number") is None

    def test_parse_row_none_input(self, parser):
        assert parser._parse_row(None) is None

    def test_parse_row_empty_input(self, parser):
        assert parser._parse_row([]) is None


# =========================================================================
# DeelParser
# =========================================================================

class TestDeelParser:

    @pytest.fixture
    def parser(self):
        return DeelParser()

    def test_parse_csv_row_income(self, parser):
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "completed",
            "Transaction Type": "client_payment",
            "Currency": "EUR",
            "Transaction Amount": "1000.00",
            "Provider Fee": "5.00",
            "Client": "ACME Corp",
            "Contract Name": "Development Contract",
            "Withdraw Method": "",
            "Withdraw Method Custom Name": "",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is not None
        assert result.amount == 1000.00
        assert result.transaction_type == TransactionType.INCOME
        assert result.bank_type == BankType.DEEL
        assert "ACME Corp" in result.description
        assert "[EUR]" in result.description

    def test_parse_csv_row_withdrawal(self, parser):
        row = {
            "Date Requested": "2025-01-20 14:30:00",
            "Transaction Status": "completed",
            "Transaction Type": "withdrawal",
            "Currency": "USD",
            "Transaction Amount": "-500.00",
            "Provider Fee": "3.00",
            "Client": "",
            "Contract Name": "",
            "Withdraw Method": "payoneer",
            "Withdraw Method Custom Name": "My Payoneer",
        }

        result = parser._parse_csv_row(row, 3)

        assert result is not None
        assert result.amount == 500.00
        assert result.transaction_type == TransactionType.EXPENSE
        assert "My Payoneer" in result.description

    def test_parse_csv_row_skips_non_completed(self, parser):
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "cancelled",
            "Transaction Type": "client_payment",
            "Currency": "EUR",
            "Transaction Amount": "1000.00",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is None

    def test_parse_csv_row_invalid_date(self, parser):
        row = {
            "Date Requested": "not-a-date",
            "Transaction Status": "completed",
            "Transaction Type": "client_payment",
            "Currency": "EUR",
            "Transaction Amount": "1000.00",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is None

    def test_parse_csv_row_invalid_amount(self, parser):
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "completed",
            "Transaction Type": "client_payment",
            "Currency": "EUR",
            "Transaction Amount": "abc",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is None

    def test_parse_csv_row_zero_amount(self, parser):
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "completed",
            "Transaction Type": "client_payment",
            "Currency": "EUR",
            "Transaction Amount": "0",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is None

    def test_parse_deel_date_datetime_format(self, parser):
        result = parser._parse_deel_date("2025-01-15 10:00:00")
        assert result == date(2025, 1, 15)

    def test_parse_deel_date_date_only(self, parser):
        result = parser._parse_deel_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_parse_deel_date_invalid(self, parser):
        assert parser._parse_deel_date("invalid") is None

    def test_parse_deel_date_empty(self, parser):
        assert parser._parse_deel_date("") is None

    def test_sanitize_field_strips_formula_chars(self, parser):
        assert parser._sanitize_field("=CMD") == "CMD"
        assert parser._sanitize_field("+TEXT") == "TEXT"
        assert parser._sanitize_field("@FORMULA") == "FORMULA"
        assert parser._sanitize_field("normal") == "normal"

    def test_build_description_income_with_client_and_contract(self, parser):
        row = {"Client": "ACME", "Contract Name": "Dev"}
        desc = parser._build_description(row, TransactionType.INCOME)
        assert desc == "[Payment] ACME — Dev"

    def test_build_description_income_client_only(self, parser):
        row = {"Client": "ACME", "Contract Name": ""}
        desc = parser._build_description(row, TransactionType.INCOME)
        assert desc == "[Payment] ACME"

    def test_build_description_income_contract_only(self, parser):
        row = {"Client": "", "Contract Name": "Dev Contract"}
        desc = parser._build_description(row, TransactionType.INCOME)
        assert desc == "[Payment] Dev Contract"

    def test_build_description_income_no_details(self, parser):
        row = {"Client": "", "Contract Name": ""}
        desc = parser._build_description(row, TransactionType.INCOME)
        assert desc == "Deel payment"

    def test_build_description_expense_with_custom_name(self, parser):
        row = {
            "Withdraw Method": "payoneer",
            "Withdraw Method Custom Name": "My Account",
        }
        desc = parser._build_description(row, TransactionType.EXPENSE)
        assert desc == "[Withdrawal] My Account"

    def test_build_description_expense_method_only(self, parser):
        row = {
            "Withdraw Method": "bank_transfer",
            "Withdraw Method Custom Name": "",
        }
        desc = parser._build_description(row, TransactionType.EXPENSE)
        assert desc == "[Withdrawal] bank_transfer"

    def test_build_description_expense_no_details(self, parser):
        row = {
            "Withdraw Method": "",
            "Withdraw Method Custom Name": "",
        }
        desc = parser._build_description(row, TransactionType.EXPENSE)
        assert desc == "[Withdrawal] withdrawal"

    def test_parse_csv_row_unknown_type_positive_is_income(self, parser):
        """Unknown transaction type with positive amount infers INCOME."""
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "completed",
            "Transaction Type": "refund",
            "Currency": "EUR",
            "Transaction Amount": "50.00",
            "Client": "",
            "Contract Name": "",
            "Withdraw Method": "",
            "Withdraw Method Custom Name": "",
            "Provider Fee": "",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is not None
        assert result.transaction_type == TransactionType.INCOME

    def test_parse_csv_row_unknown_type_negative_is_expense(self, parser):
        """Unknown transaction type with negative amount infers EXPENSE."""
        row = {
            "Date Requested": "2025-01-15 10:00:00",
            "Transaction Status": "completed",
            "Transaction Type": "adjustment",
            "Currency": "EUR",
            "Transaction Amount": "-50.00",
            "Client": "",
            "Contract Name": "",
            "Withdraw Method": "",
            "Withdraw Method Custom Name": "",
            "Provider Fee": "",
        }

        result = parser._parse_csv_row(row, 2)

        assert result is not None
        assert result.transaction_type == TransactionType.EXPENSE

    @pytest.mark.asyncio
    async def test_parse_pdf_from_csv_file(self, parser, tmp_path):
        """Integration: parse an actual CSV file on disk."""
        csv_file = tmp_path / "deel.csv"
        csv_file.write_text(
            "Date Requested,Transaction Status,Transaction Type,"
            "Currency,Transaction Amount,Provider Fee,"
            "Client,Contract Name,Withdraw Method,Withdraw Method Custom Name\n"
            "2025-01-15 10:00:00,completed,client_payment,"
            "EUR,1000.00,5.00,"
            "ACME Corp,Dev Contract,,\n"
            "2025-01-20 14:30:00,cancelled,withdrawal,"
            "USD,-500.00,3.00,"
            ",,payoneer,My Account\n"
            "2025-01-25 09:00:00,completed,withdrawal,"
            "USD,-200.00,2.00,"
            ",,bank_transfer,My Bank\n",
            encoding="utf-8",
        )

        transactions = await parser.parse_pdf(str(csv_file), "en", 1)

        # Only completed transactions: 1 income + 1 withdrawal
        assert len(transactions) == 2
        assert transactions[0].transaction_type == TransactionType.INCOME
        assert transactions[1].transaction_type == TransactionType.EXPENSE
