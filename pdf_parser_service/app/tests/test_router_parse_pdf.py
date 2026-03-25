"""
Tests for the POST /pdf/parse endpoint.

Covers:
- Successful PDF/XLSX/CSV upload and parsing
- File type validation (MIME type and magic bytes)
- File size validation
- Language parameter validation
- Bank type validation
- Monthly upload limit enforcement
- Records-per-upload limit enforcement
- Error handling for parsing failures
- Temp file cleanup
"""

import io
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.models.transaction import BankType, PDFParseResponse


class TestParsePdfSuccess:
    """Tests for successful PDF parsing."""

    def test_parse_pdf_success(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("statement.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_transactions"] == 2
        assert data["bank_detected"] == "monobank"
        assert len(data["transactions"]) == 2

    def test_parse_pdf_with_bank_type(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("statement.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"bank_type": "monobank", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_parse_xlsx_success(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_xlsx_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={
                "file": (
                    "statement.xlsx",
                    io.BytesIO(valid_xlsx_content),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"bank_type": "privatbank", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_parse_csv_success(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_csv_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("transactions.csv", io.BytesIO(valid_csv_content), "text/csv")},
            data={"bank_type": "deel", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_parse_pdf_default_language(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        """Language defaults to 'en' when not provided."""
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("statement.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_parse_pdf_limit_info_in_response(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        """Response includes limit_info after successful parse."""
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("statement.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["limit_info"] is not None
        assert data["limit_info"]["uploads_per_month"] == 10
        assert data["limit_info"]["plan_code"] == "professional"
        assert data["limit_info"]["uploads_used_this_month"] == 1

    def test_upload_record_created_on_success(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        """A successful upload creates a record in the database."""
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        client.post(
            "/pdf/parse",
            files={"file": ("statement.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "en"},
        )

        mock_upload_repo.create_upload_record.assert_called_once()
        call_kwargs = mock_upload_repo.create_upload_record.call_args
        assert call_kwargs.kwargs["status"] == "success"


class TestParsePdfFileValidation:
    """Tests for file type and content validation."""

    def test_reject_unsupported_mime_type(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        response = client.post(
            "/pdf/parse",
            files={"file": ("image.png", io.BytesIO(b"\x89PNG"), "image/png")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "PDF, XLSX, and CSV" in response.json()["error"]

    def test_reject_invalid_pdf_magic_bytes(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        response = client.post(
            "/pdf/parse",
            files={"file": ("fake.pdf", io.BytesIO(b"NOT A PDF"), "application/pdf")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a valid PDF" in response.json()["error"]

    def test_reject_invalid_xlsx_magic_bytes(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        response = client.post(
            "/pdf/parse",
            files={
                "file": (
                    "fake.xlsx",
                    io.BytesIO(b"NOT XLSX"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a valid XLSX" in response.json()["error"]

    def test_reject_invalid_csv_content(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        # Non-UTF-8 bytes pretending to be CSV
        response = client.post(
            "/pdf/parse",
            files={"file": ("fake.csv", io.BytesIO(b"\xff\xfe\x00\x01\x80\x81"), "text/csv")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a valid CSV" in response.json()["error"]

    def test_reject_file_exceeding_max_size(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        with patch("app.routers.pdf_parser.settings") as mock_settings:
            mock_settings.max_file_size = 100  # 100 bytes
            mock_settings.upload_directory = "/tmp/test_uploads"

            large_content = b"%PDF-" + b"x" * 200
            response = client.post(
                "/pdf/parse",
                files={"file": ("big.pdf", io.BytesIO(large_content), "application/pdf")},
                data={"language": "en"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "size exceeds" in response.json()["error"]


class TestParsePdfLanguageValidation:
    """Tests for language parameter validation."""

    def test_reject_invalid_language(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
    ):
        response = client.post(
            "/pdf/parse",
            files={"file": ("stmt.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"language": "fr"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid language" in response.json()["error"]

    def test_accept_language_ru(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "ru"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_accept_language_uk(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            return_value=sample_parse_response
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "uk"},
        )

        assert response.status_code == status.HTTP_200_OK


class TestParsePdfBankTypeValidation:
    """Tests for bank_type parameter validation."""

    def test_reject_unsupported_bank_type(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        valid_pdf_content,
    ):
        response = client.post(
            "/pdf/parse",
            files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"bank_type": "nonexistent_bank", "language": "en"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported bank type" in response.json()["error"]


class TestParsePdfUploadLimits:
    """Tests for subscription-based upload limits."""

    def test_reject_when_monthly_upload_limit_exceeded(
        self,
        client: TestClient,
        mock_upload_repo,
        valid_pdf_content,
    ):
        with patch("app.routers.pdf_parser.subscription_client") as mock_sub:
            mock_sub.check_pdf_upload_limit.return_value = False
            mock_sub.get_user_features.return_value = {
                "pdf_uploads_per_month": {
                    "feature_code": "pdf_uploads_per_month",
                    "enabled": True,
                    "limit_value": 1,
                    "plan_code": "basic",
                }
            }
            mock_upload_repo.get_monthly_upload_count.return_value = 1

            response = client.post(
                "/pdf/parse",
                files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
                data={"language": "en"},
            )

            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            data = response.json()
            # HTTPException detail is wrapped by http_exception_handler as {"error": detail}
            error_detail = data.get("error", data.get("detail", {}))
            assert "PDF_UPLOAD_LIMIT_EXCEEDED" in str(error_detail)

    def test_reject_when_records_per_upload_limit_exceeded(
        self,
        client: TestClient,
        mock_upload_repo,
        mock_pdf_parser_service,
        sample_parse_response,
        valid_pdf_content,
    ):
        with patch("app.routers.pdf_parser.subscription_client") as mock_sub:
            mock_sub.check_pdf_upload_limit.return_value = True
            mock_sub.check_pdf_records_limit.return_value = False
            mock_sub.get_user_features.return_value = {
                "pdf_uploads_per_month": {
                    "enabled": True,
                    "limit_value": 10,
                    "plan_code": "basic",
                },
                "pdf_records_per_upload": {
                    "enabled": True,
                    "limit_value": 1,
                    "plan_code": "basic",
                },
            }

            sample_parse_response.total_transactions = 50
            mock_pdf_parser_service.parse_pdf = AsyncMock(
                return_value=sample_parse_response
            )

            response = client.post(
                "/pdf/parse",
                files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
                data={"language": "en"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            error_detail = data.get("error", data.get("detail", {}))
            assert "PDF_RECORDS_LIMIT_EXCEEDED" in str(error_detail)

    def test_failed_upload_creates_record(
        self,
        client: TestClient,
        mock_upload_repo,
        valid_pdf_content,
    ):
        """A failed upload due to limit still creates a failed record."""
        with patch("app.routers.pdf_parser.subscription_client") as mock_sub:
            mock_sub.check_pdf_upload_limit.return_value = False
            mock_sub.get_user_features.return_value = {
                "pdf_uploads_per_month": {
                    "enabled": True,
                    "limit_value": 1,
                    "plan_code": "basic",
                }
            }
            mock_upload_repo.get_monthly_upload_count.return_value = 1

            client.post(
                "/pdf/parse",
                files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
                data={"language": "en"},
            )

            mock_upload_repo.create_upload_record.assert_called_once()
            call_kwargs = mock_upload_repo.create_upload_record.call_args
            assert call_kwargs.kwargs["status"] == "failed"


class TestParsePdfErrorHandling:
    """Tests for error handling during parsing."""

    def test_internal_error_returns_500(
        self,
        client: TestClient,
        mock_subscription_client,
        mock_upload_repo,
        mock_pdf_parser_service,
        valid_pdf_content,
    ):
        mock_pdf_parser_service.parse_pdf = AsyncMock(
            side_effect=RuntimeError("Unexpected failure")
        )

        response = client.post(
            "/pdf/parse",
            files={"file": ("stmt.pdf", io.BytesIO(valid_pdf_content), "application/pdf")},
            data={"language": "en"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to process PDF" in response.json()["error"]
