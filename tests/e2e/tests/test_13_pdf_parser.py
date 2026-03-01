"""E2E tests for PDF parser service: health, supported banks, auth gating, upload validation."""
import pytest

pytestmark = pytest.mark.pdf_parser


class TestPdfParserHealth:

    async def test_health_check(self, pdf_parser_client):
        result = await pdf_parser_client.pdf_health()
        data = result.raise_on_error()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf-parser"
        assert data["supported_banks"] >= 1


class TestSupportedBanks:

    async def test_get_supported_banks(self, pdf_parser_client):
        result = await pdf_parser_client.get_supported_banks()
        data = result.raise_on_error()
        assert "supported_banks" in data
        assert "total_count" in data
        assert data["total_count"] >= 1
        assert isinstance(data["supported_banks"], list)

    async def test_get_languages_for_bank(self, pdf_parser_client):
        # First get the list of banks to use a real bank name
        banks = (await pdf_parser_client.get_supported_banks()).raise_on_error()
        if banks["total_count"] > 0:
            bank_name = banks["supported_banks"][0]
            result = await pdf_parser_client.get_languages(bank_name)
            data = result.raise_on_error()
            assert "available_languages" in data
            assert data["total_languages"] >= 1

    async def test_get_languages_unknown_bank(self, pdf_parser_client):
        result = await pdf_parser_client.get_languages("nonexistent_bank_xyz")
        assert not result.ok


class TestPdfUploadValidation:

    async def test_upload_invalid_file_type(self, pdf_parser_client):
        """Uploading a non-PDF/XLSX/CSV file should be rejected."""
        result = await pdf_parser_client.parse_pdf(
            file_content=b"this is not a pdf",
            filename="test.txt",
            content_type="text/plain",
        )
        assert not result.ok

    async def test_upload_fake_pdf(self, pdf_parser_client):
        """Uploading a file with PDF MIME but invalid content should be rejected."""
        result = await pdf_parser_client.parse_pdf(
            file_content=b"this is not really a pdf",
            filename="fake.pdf",
            content_type="application/pdf",
        )
        assert not result.ok

    async def test_upload_invalid_language(self, pdf_parser_client):
        """Uploading with an invalid language should be rejected."""
        # Create a minimal valid PDF header to pass MIME check, language should fail
        pdf_header = b"%PDF-1.4 fake content"
        result = await pdf_parser_client.parse_pdf(
            file_content=pdf_header,
            filename="test.pdf",
            content_type="application/pdf",
            language="zz",
        )
        assert not result.ok


class TestPdfAuthGating:

    async def test_unauthenticated_parse_rejected(self, unauthenticated_pdf_client):
        """Parsing without auth token should fail."""
        result = await unauthenticated_pdf_client.parse_pdf(
            file_content=b"%PDF-1.4 content",
            filename="test.pdf",
            content_type="application/pdf",
        )
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_unauthenticated_supported_banks_rejected(self, unauthenticated_pdf_client):
        """Getting supported banks without auth should fail."""
        result = await unauthenticated_pdf_client.get_supported_banks()
        assert not result.ok
        assert result.status_code in (401, 403)
