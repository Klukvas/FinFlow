"""
Tests for PDFParserService business logic.

Covers:
- Routing to correct parser based on bank_type
- File existence validation
- Timeout handling (ParsingTimeoutError)
- Unexpected error wrapping (PDFParsingError)
- Response structure (PDFParseResponse fields)
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.models.transaction import (
    BankType,
    ParsedTransaction,
    TransactionType,
    PDFParseResponse,
)
from app.services.pdf_parser import PDFParserService
from app.exceptions import (
    FileProcessingError,
    PDFParsingError,
    UnsupportedBankError,
    ParsingTimeoutError,
    ErrorCodes,
)
from datetime import date


@pytest.fixture
def service():
    """Create a PDFParserService with mocked parsers."""
    svc = PDFParserService()
    svc.monobank_parser = MagicMock()
    svc.privatbank_parser = MagicMock()
    svc.ukrsib_parser = MagicMock()
    svc.abank_parser = MagicMock()
    svc.deel_parser = MagicMock()
    return svc


@pytest.fixture
def fake_transaction():
    return ParsedTransaction(
        amount=50.0,
        description="Test",
        transaction_date=date(2025, 3, 1),
        transaction_type=TransactionType.EXPENSE,
        bank_type=BankType.MONOBANK,
        raw_text="raw",
        confidence_score=0.9,
    )


class TestParsePdfRouting:
    """Tests for bank-type routing in parse_pdf."""

    @pytest.mark.asyncio
    async def test_routes_to_monobank_parser(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)

        assert result.bank_detected == BankType.MONOBANK
        service.monobank_parser.parse_pdf.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_routes_to_privatbank_parser(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.xlsx"
        file_path.write_bytes(b"PK\x03\x04 content")

        service.privatbank_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), BankType.PRIVATBANK, "en", 1)

        assert result.bank_detected == BankType.PRIVATBANK
        service.privatbank_parser.parse_pdf.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_routes_to_ukrsibbank_parser(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.ukrsib_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), BankType.UKRSIBBANK, "en", 1)

        assert result.bank_detected == BankType.UKRSIBBANK

    @pytest.mark.asyncio
    async def test_routes_to_abank_parser(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.abank_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), BankType.ABANK, "en", 1)

        assert result.bank_detected == BankType.ABANK

    @pytest.mark.asyncio
    async def test_routes_to_deel_parser(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("header\n")

        service.deel_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), BankType.DEEL, "en", 1)

        assert result.bank_detected == BankType.DEEL

    @pytest.mark.asyncio
    async def test_auto_detect_defaults_to_monobank(self, service, fake_transaction, tmp_path):
        """When bank_type is None, defaults to monobank parser."""
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(return_value=[fake_transaction])

        result = await service.parse_pdf(str(file_path), None, "en", 1)

        assert result.bank_detected == BankType.MONOBANK
        service.monobank_parser.parse_pdf.assert_awaited_once()


class TestParsePdfFileValidation:
    """Tests for file existence validation."""

    @pytest.mark.asyncio
    async def test_file_not_found_raises_error(self, service):
        with pytest.raises(FileProcessingError) as exc_info:
            await service.parse_pdf("/nonexistent/path.pdf", BankType.MONOBANK, "en", 1)

        assert exc_info.value.error_code == ErrorCodes.FILE_NOT_FOUND


class TestParsePdfTimeout:
    """Tests for parsing timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_raises_parsing_timeout_error(self, service, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with pytest.raises(ParsingTimeoutError):
            await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)


class TestParsePdfResponseStructure:
    """Tests for response structure validation."""

    @pytest.mark.asyncio
    async def test_response_has_correct_metadata(self, service, fake_transaction, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(
            return_value=[fake_transaction, fake_transaction]
        )

        result = await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)

        assert result.total_transactions == 2
        assert result.successful_parses == 2
        assert result.failed_parses == 0
        assert "file_size" in result.parsing_metadata
        assert result.parsing_metadata["parsing_method"] == "monobank_parser"

    @pytest.mark.asyncio
    async def test_empty_parse_returns_zero_transactions(self, service, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(return_value=[])

        result = await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)

        assert result.total_transactions == 0
        assert result.transactions == []


class TestParsePdfErrorWrapping:
    """Tests for unexpected error wrapping."""

    @pytest.mark.asyncio
    async def test_unexpected_error_wrapped_as_pdf_parsing_error(self, service, tmp_path):
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        service.monobank_parser.parse_pdf = AsyncMock(
            side_effect=ValueError("Something went wrong")
        )

        with pytest.raises(PDFParsingError) as exc_info:
            await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)

        assert exc_info.value.error_code == ErrorCodes.PDF_PARSING_FAILED

    @pytest.mark.asyncio
    async def test_known_exceptions_not_wrapped(self, service, tmp_path):
        """FileProcessingError should be re-raised, not wrapped."""
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 content")

        original_error = FileProcessingError("Bad file", ErrorCodes.INVALID_PDF_FORMAT)
        service.monobank_parser.parse_pdf = AsyncMock(side_effect=original_error)

        with pytest.raises(FileProcessingError) as exc_info:
            await service.parse_pdf(str(file_path), BankType.MONOBANK, "en", 1)

        assert exc_info.value is original_error


class TestCleanup:
    """Tests for service cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_closes_category_client(self, service):
        mock_client = AsyncMock()
        service.monobank_parser.category_client = mock_client

        await service.cleanup()

        mock_client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cleanup_without_category_client(self, service):
        """Cleanup should not fail if category_client is missing."""
        if hasattr(service.monobank_parser, "category_client"):
            delattr(service.monobank_parser, "category_client")

        # Should not raise
        await service.cleanup()
