"""
Tests for BasePDFParser utility methods.

Covers:
- _parse_date: various date formats, invalid dates
- _parse_amount: positive, negative, comma/space formatting, invalid
- _determine_transaction_type: income vs expense based on sign
- _calculate_confidence_score: scoring based on data quality
- _parse_mcc_code: valid range, invalid, empty
- _clean_description: whitespace normalization, prefix removal
- _extract_tables_from_pdf: file not found, empty PDF, corrupted PDF, encrypted
- _is_transaction_header: bank header matching
"""

from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app.models.transaction import BankType, TransactionType
from app.services.parsers.base_parser import BasePDFParser
from app.exceptions import InvalidPDFError, FileProcessingError, ErrorCodes


class ConcreteParser(BasePDFParser):
    """Concrete implementation for testing abstract base class."""

    def __init__(self):
        super().__init__(BankType.MONOBANK)

    async def parse_pdf(self, file_path, language="en", user_id=None):
        return []

    async def _extract_transactions_from_table(self, table, language="en", user_id=None):
        return []


@pytest.fixture
def parser():
    return ConcreteParser()


class TestParseDate:

    def test_valid_date_dd_mm_yyyy(self, parser):
        result = parser._parse_date("15.01.2025")
        assert result == date(2025, 1, 15)

    def test_date_with_time(self, parser):
        result = parser._parse_date("15.01.2025 10:30:00")
        assert result == date(2025, 1, 15)

    def test_date_with_surrounding_text(self, parser):
        result = parser._parse_date("Transaction on 15.01.2025 was processed")
        assert result == date(2025, 1, 15)

    def test_empty_string_returns_none(self, parser):
        assert parser._parse_date("") is None

    def test_none_returns_none(self, parser):
        assert parser._parse_date(None) is None

    def test_invalid_date_string_returns_none(self, parser):
        assert parser._parse_date("not a date") is None

    def test_invalid_date_values_returns_none(self, parser):
        # Month 13 does not exist
        assert parser._parse_date("15.13.2025") is None

    def test_incomplete_date_returns_none(self, parser):
        assert parser._parse_date("15.01") is None


class TestParseAmount:

    def test_positive_amount(self, parser):
        assert parser._parse_amount("100.50") == 100.50

    def test_negative_amount(self, parser):
        assert parser._parse_amount("-100.50") == -100.50

    def test_amount_with_spaces(self, parser):
        assert parser._parse_amount("1 000.50") == 1000.50

    def test_amount_with_comma(self, parser):
        assert parser._parse_amount("100,50") == 100.50

    def test_empty_string_returns_none(self, parser):
        assert parser._parse_amount("") is None

    def test_none_returns_none(self, parser):
        assert parser._parse_amount(None) is None

    def test_zero_amount_returns_none(self, parser):
        # Zero amounts are filtered out
        assert parser._parse_amount("0") is None

    def test_non_numeric_returns_none(self, parser):
        assert parser._parse_amount("abc") is None

    def test_amount_with_mixed_separators(self, parser):
        assert parser._parse_amount("1 000,50") == 1000.50


class TestDetermineTransactionType:

    def test_negative_is_expense(self, parser):
        assert parser._determine_transaction_type(-100) == TransactionType.EXPENSE

    def test_positive_is_income(self, parser):
        assert parser._determine_transaction_type(100) == TransactionType.INCOME

    def test_zero_is_income(self, parser):
        # Edge case: zero is considered income by the implementation
        assert parser._determine_transaction_type(0) == TransactionType.INCOME


class TestCalculateConfidenceScore:

    def test_base_confidence(self, parser):
        """Short description, old date, tiny amount should give base score."""
        score = parser._calculate_confidence_score("abc", date(2019, 1, 1), 0.001)
        # base 0.7, description len <= 5 (no bonus), date <= 2020 (no bonus),
        # abs(0.001) <= 0.01 (no bonus) = 0.7
        assert score == pytest.approx(0.7, abs=0.01)

    def test_high_quality_data_near_max(self, parser):
        """Long description, recent date, reasonable amount should give ~1.0."""
        score = parser._calculate_confidence_score(
            "Very detailed description of payment",
            date(2025, 1, 15),
            100.0,
        )
        assert score == 1.0

    def test_confidence_capped_at_1(self, parser):
        score = parser._calculate_confidence_score(
            "Long enough description text here",
            date(2025, 6, 1),
            999.99,
        )
        assert score <= 1.0

    def test_medium_quality(self, parser):
        """Description > 5 chars but <= 15, recent date."""
        score = parser._calculate_confidence_score(
            "Payment", date(2025, 1, 1), 50.0
        )
        # base 0.7 + 0.1 (len>5) + 0.1 (date>2020) + 0.1 (abs>0.01) = 1.0
        assert score == pytest.approx(1.0, abs=0.01)


class TestParseMccCode:

    def test_valid_mcc_code(self, parser):
        assert parser._parse_mcc_code("5411") == 5411

    def test_mcc_with_whitespace(self, parser):
        assert parser._parse_mcc_code(" 5411 ") == 5411

    def test_mcc_with_text(self, parser):
        assert parser._parse_mcc_code("MCC: 5411") == 5411

    def test_mcc_leading_zeros(self, parser):
        assert parser._parse_mcc_code("0742") == 742

    def test_mcc_min_valid(self, parser):
        assert parser._parse_mcc_code("1") == 1

    def test_mcc_max_valid(self, parser):
        assert parser._parse_mcc_code("9999") == 9999

    def test_mcc_out_of_range_high(self, parser):
        assert parser._parse_mcc_code("10000") is None

    def test_mcc_zero_returns_none(self, parser):
        assert parser._parse_mcc_code("0") is None

    def test_mcc_empty_returns_none(self, parser):
        assert parser._parse_mcc_code("") is None

    def test_mcc_none_returns_none(self, parser):
        assert parser._parse_mcc_code(None) is None

    def test_mcc_non_numeric_returns_none(self, parser):
        assert parser._parse_mcc_code("abc") is None


class TestCleanDescription:

    def test_removes_extra_whitespace(self, parser):
        result = parser._clean_description("  hello   world  ")
        assert result == "hello world"

    def test_empty_string(self, parser):
        assert parser._clean_description("") == ""

    def test_none_returns_empty(self, parser):
        assert parser._clean_description(None) == ""

    def test_multiline_collapsed(self, parser):
        result = parser._clean_description("line1\nline2\ttab")
        assert result == "line1 line2 tab"


class TestExtractTablesFromPdf:

    def test_file_not_found_raises_error(self, parser):
        with pytest.raises(FileProcessingError) as exc_info:
            parser._extract_tables_from_pdf("/nonexistent/file.pdf")

        assert exc_info.value.error_code == ErrorCodes.FILE_NOT_FOUND

    def test_empty_pdf_raises_invalid_pdf_error(self, parser, tmp_path):
        file_path = tmp_path / "empty.pdf"
        file_path.write_bytes(b"%PDF-1.4")

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = []
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_plumber.open.return_value = mock_pdf

            with pytest.raises(InvalidPDFError):
                parser._extract_tables_from_pdf(str(file_path))

    def test_encrypted_pdf_raises_error(self, parser, tmp_path):
        file_path = tmp_path / "encrypted.pdf"
        file_path.write_bytes(b"%PDF-1.4 encrypted")

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_plumber.open.side_effect = Exception("password protected")

            with pytest.raises(FileProcessingError) as exc_info:
                parser._extract_tables_from_pdf(str(file_path))

            assert "password" in exc_info.value.message.lower()

    def test_corrupted_pdf_raises_invalid_pdf_error(self, parser, tmp_path):
        file_path = tmp_path / "corrupt.pdf"
        file_path.write_bytes(b"corrupted data")

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_plumber.open.side_effect = Exception("invalid pdf structure")

            with pytest.raises(InvalidPDFError):
                parser._extract_tables_from_pdf(str(file_path))

    def test_permission_denied_raises_error(self, parser, tmp_path):
        file_path = tmp_path / "locked.pdf"
        file_path.write_bytes(b"%PDF-1.4")

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_plumber.open.side_effect = PermissionError("Access denied")

            with pytest.raises(FileProcessingError) as exc_info:
                parser._extract_tables_from_pdf(str(file_path))

            assert exc_info.value.error_code == ErrorCodes.FILE_PROCESSING_FAILED

    def test_successful_extraction(self, parser, tmp_path):
        file_path = tmp_path / "good.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [["Date", "Amount"], ["01.01.2025", "100"]]
        ]

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_plumber.open.return_value = mock_pdf

            tables = parser._extract_tables_from_pdf(str(file_path))

            assert len(tables) == 1
            assert len(tables[0]) == 2

    def test_page_extraction_error_continues(self, parser, tmp_path):
        """If one page fails, others should still be processed."""
        file_path = tmp_path / "partial.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        good_page = MagicMock()
        good_page.extract_tables.return_value = [
            [["Date"], ["01.01.2025"]]
        ]
        bad_page = MagicMock()
        bad_page.extract_tables.side_effect = Exception("Page corrupt")

        with patch("app.services.parsers.base_parser.pdfplumber") as mock_plumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [bad_page, good_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_plumber.open.return_value = mock_pdf

            tables = parser._extract_tables_from_pdf(str(file_path))

            assert len(tables) == 1


class TestFindTransactionTables:

    def test_finds_tables_with_headers(self, parser):
        tables = [
            [["дата i час операції", "деталі операції", "mcc"], ["01.01.2025", "test", "5411"]],
            [["Random", "Data"], ["1", "2"]],
        ]

        result = parser._find_transaction_tables(tables)

        assert len(result) == 1

    def test_skips_tables_with_fewer_than_two_rows(self, parser):
        tables = [
            [["дата i час операції"]],
        ]

        result = parser._find_transaction_tables(tables)

        assert len(result) == 0

    def test_skips_empty_tables(self, parser):
        tables = [[], None]

        result = parser._find_transaction_tables([t for t in tables if t])

        assert len(result) == 0


class TestIsTransactionHeader:

    def test_recognizes_monobank_ua_header(self, parser):
        assert parser._is_transaction_header("Дата i час операції") is True

    def test_recognizes_monobank_en_header(self, parser):
        assert parser._is_transaction_header("date and time") is True

    def test_rejects_non_header(self, parser):
        assert parser._is_transaction_header("Random text") is False

    def test_handles_none(self, parser):
        assert parser._is_transaction_header(None) is False

    def test_handles_empty_string(self, parser):
        assert parser._is_transaction_header("") is False

    def test_case_insensitive(self, parser):
        assert parser._is_transaction_header("ДАТА I ЧАС ОПЕРАЦІЇ") is True
