"""
Tests for custom exceptions and exception handlers.

Covers:
- Exception classes: message formatting, attributes
- Limit exceptions: PDFUploadLimitExceededError, PDFRecordsLimitExceededError
- Exception handlers: response format and status codes
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from fastapi import HTTPException

from app.exceptions import (
    PDFParsingError,
    UnsupportedBankError,
    FileProcessingError,
    InvalidPDFError,
    ParsingTimeoutError,
    BankNotFoundError,
    ErrorCodes,
)
from app.exceptions.limit_exceptions import (
    PDFUploadLimitExceededError,
    PDFRecordsLimitExceededError,
)
from app.exception_handlers import (
    custom_validation_exception_handler,
    pdf_parsing_error_handler,
    unsupported_bank_handler,
    file_processing_error_handler,
    bank_not_found_handler,
    http_exception_handler,
)


# =========================================================================
# Exception Classes
# =========================================================================

class TestPDFParsingError:

    def test_message_and_code(self):
        err = PDFParsingError("Parse failed", ErrorCodes.PDF_PARSING_FAILED)
        assert err.message == "Parse failed"
        assert err.error_code == ErrorCodes.PDF_PARSING_FAILED
        assert err.details == {}

    def test_with_details(self):
        err = PDFParsingError("Failed", ErrorCodes.PDF_PARSING_FAILED, {"page": 3})
        assert err.details == {"page": 3}


class TestUnsupportedBankError:

    def test_message_includes_bank_and_supported(self):
        err = UnsupportedBankError("mybank", ["monobank", "privatbank"])
        assert "mybank" in err.message
        assert "monobank" in err.message
        assert err.bank_type == "mybank"
        assert err.supported_banks == ["monobank", "privatbank"]
        assert err.error_code == ErrorCodes.UNSUPPORTED_BANK_TYPE


class TestFileProcessingError:

    def test_default_error_code(self):
        err = FileProcessingError("Something failed")
        assert err.error_code == ErrorCodes.FILE_PROCESSING_FAILED

    def test_custom_error_code(self):
        err = FileProcessingError("Too big", ErrorCodes.FILE_SIZE_EXCEEDED)
        assert err.error_code == ErrorCodes.FILE_SIZE_EXCEEDED

    def test_file_name_attribute(self):
        err = FileProcessingError("Bad file", file_name="test.pdf")
        assert err.file_name == "test.pdf"


class TestInvalidPDFError:

    def test_message_with_filename(self):
        err = InvalidPDFError("test.pdf")
        assert "test.pdf" in err.message
        assert err.error_code == ErrorCodes.INVALID_PDF_FORMAT

    def test_message_without_filename(self):
        err = InvalidPDFError()
        assert "Invalid or corrupted PDF" in err.message


class TestParsingTimeoutError:

    def test_message_with_seconds(self):
        err = ParsingTimeoutError(30)
        assert "30" in err.message
        assert err.timeout_seconds == 30
        assert err.error_code == ErrorCodes.PDF_PARSING_TIMEOUT


class TestBankNotFoundError:

    def test_message_with_bank_name(self):
        err = BankNotFoundError("fakebobank")
        assert "fakebobank" in err.message
        assert err.bank_name == "fakebobank"
        assert err.error_code == ErrorCodes.BANK_NOT_FOUND


class TestPDFUploadLimitExceededError:

    def test_attributes(self):
        err = PDFUploadLimitExceededError(5, 5)
        assert err.current_count == 5
        assert err.limit == 5
        assert "5/5" in str(err)

    def test_message_format(self):
        err = PDFUploadLimitExceededError(3, 3)
        assert "Monthly PDF upload limit exceeded" in str(err)


class TestPDFRecordsLimitExceededError:

    def test_attributes(self):
        err = PDFRecordsLimitExceededError(50, 20)
        assert err.record_count == 50
        assert err.limit == 20
        assert "50" in str(err)
        assert "20" in str(err)


# =========================================================================
# Exception Handlers
# =========================================================================

class TestExceptionHandlers:

    @pytest.fixture
    def mock_request(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        exc = Exception("validation error")
        response = await custom_validation_exception_handler(mock_request, exc)
        assert response.status_code == 422
        assert b"VALIDATION_ERROR" in response.body

    @pytest.mark.asyncio
    async def test_pdf_parsing_error_handler(self, mock_request):
        exc = PDFParsingError("Parse failed", ErrorCodes.PDF_PARSING_FAILED)
        response = await pdf_parsing_error_handler(mock_request, exc)
        assert response.status_code == 400
        assert b"Parse failed" in response.body

    @pytest.mark.asyncio
    async def test_unsupported_bank_handler(self, mock_request):
        exc = UnsupportedBankError("fake", ["monobank"])
        response = await unsupported_bank_handler(mock_request, exc)
        assert response.status_code == 400
        assert b"UNSUPPORTED_BANK_TYPE" in response.body

    @pytest.mark.asyncio
    async def test_file_processing_error_handler(self, mock_request):
        exc = FileProcessingError("Bad file", ErrorCodes.INVALID_FILE_TYPE)
        response = await file_processing_error_handler(mock_request, exc)
        assert response.status_code == 400
        assert b"Bad file" in response.body

    @pytest.mark.asyncio
    async def test_bank_not_found_handler(self, mock_request):
        exc = BankNotFoundError("unknown_bank")
        response = await bank_not_found_handler(mock_request, exc)
        assert response.status_code == 404
        assert b"unknown_bank" in response.body

    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        exc = HTTPException(status_code=403, detail="Forbidden")
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 403
        assert b"Forbidden" in response.body


# =========================================================================
# ErrorCodes constants
# =========================================================================

class TestErrorCodes:

    def test_file_codes_exist(self):
        assert ErrorCodes.FILE_NOT_FOUND == "FILE_NOT_FOUND"
        assert ErrorCodes.INVALID_FILE_TYPE == "INVALID_FILE_TYPE"
        assert ErrorCodes.FILE_SIZE_EXCEEDED == "FILE_SIZE_EXCEEDED"
        assert ErrorCodes.INVALID_PDF_FORMAT == "INVALID_PDF_FORMAT"

    def test_parsing_codes_exist(self):
        assert ErrorCodes.PDF_PARSING_FAILED == "PDF_PARSING_FAILED"
        assert ErrorCodes.PDF_PARSING_TIMEOUT == "PDF_PARSING_TIMEOUT"

    def test_bank_codes_exist(self):
        assert ErrorCodes.UNSUPPORTED_BANK_TYPE == "UNSUPPORTED_BANK_TYPE"
        assert ErrorCodes.BANK_NOT_FOUND == "BANK_NOT_FOUND"

    def test_validation_codes_exist(self):
        assert ErrorCodes.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCodes.INTERNAL_SERVER_ERROR == "INTERNAL_SERVER_ERROR"
