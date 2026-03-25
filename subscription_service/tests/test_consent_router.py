"""Tests for consent router endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.routers.consent import (
    record_consent,
    get_consent_history,
    get_current_consent_version,
)
from app.schemas.consent import ConsentRecordRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_consent_log(
    id: int = 1,
    subscription_id: int = 1,
    user_id: str = "user_1",
    consent_version: str = "v1.0.0",
    consent_text: str = "I agree...",
    consent_language: str = "en",
    ip_address: str = "127.0.0.1",
):
    log = MagicMock()
    log.id = id
    log.subscription_id = subscription_id
    log.user_id = user_id
    log.consent_version = consent_version
    log.consent_text = consent_text
    log.consent_language = consent_language
    log.consent_given_at = datetime.utcnow()
    log.ip_address = ip_address
    log.user_agent = "TestBrowser/1.0"
    log.browser_fingerprint = None
    log.consent_metadata = None
    log.created_at = datetime.utcnow()
    return log


def _make_http_request(host: str = "192.168.1.1", user_agent: str = "TestBrowser/1.0"):
    request = MagicMock()
    client = MagicMock()
    client.host = host
    request.client = client
    request.headers = {"user-agent": user_agent}
    return request


# ---------------------------------------------------------------------------
# record_consent
# ---------------------------------------------------------------------------


class TestRecordConsent:
    """Tests for POST /consent/{user_id}/record."""

    @patch("app.routers.consent.ConsentService")
    def test_records_consent_successfully(self, MockConsentService, mock_db):
        consent_log = _make_consent_log()

        mock_service = MagicMock()
        mock_service.record_consent.return_value = consent_log
        MockConsentService.return_value = mock_service

        request_data = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Professional",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )
        http_request = _make_http_request()

        with patch("app.routers.consent.ConsentRecordResponse") as MockResponse:
            MockResponse.model_validate.return_value = MagicMock(id=1)
            result = record_consent(
                user_id="user_1",
                request_data=request_data,
                http_request=http_request,
                db=mock_db,
            )

        mock_service.record_consent.assert_called_once_with(
            subscription_id=1,
            user_id="user_1",
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Professional",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            ip_address="192.168.1.1",
            user_agent="TestBrowser/1.0",
            browser_fingerprint=None,
        )

    @patch("app.routers.consent.ConsentService")
    def test_extracts_ip_from_request(self, MockConsentService, mock_db):
        consent_log = _make_consent_log(ip_address="10.0.0.1")
        mock_service = MagicMock()
        mock_service.record_consent.return_value = consent_log
        MockConsentService.return_value = mock_service

        request_data = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Pro",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )
        http_request = _make_http_request(host="10.0.0.1")

        with patch("app.routers.consent.ConsentRecordResponse") as MockResponse:
            MockResponse.model_validate.return_value = MagicMock()
            record_consent(
                user_id="user_1",
                request_data=request_data,
                http_request=http_request,
                db=mock_db,
            )

        call_kwargs = mock_service.record_consent.call_args.kwargs
        assert call_kwargs["ip_address"] == "10.0.0.1"

    @patch("app.routers.consent.ConsentService")
    def test_handles_missing_client(self, MockConsentService, mock_db):
        """Must use 'unknown' when request.client is None."""
        consent_log = _make_consent_log()
        mock_service = MagicMock()
        mock_service.record_consent.return_value = consent_log
        MockConsentService.return_value = mock_service

        request_data = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Pro",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )
        http_request = MagicMock()
        http_request.client = None
        http_request.headers = {"user-agent": "Bot/1.0"}

        with patch("app.routers.consent.ConsentRecordResponse") as MockResponse:
            MockResponse.model_validate.return_value = MagicMock()
            record_consent(
                user_id="user_1",
                request_data=request_data,
                http_request=http_request,
                db=mock_db,
            )

        call_kwargs = mock_service.record_consent.call_args.kwargs
        assert call_kwargs["ip_address"] == "unknown"

    @patch("app.routers.consent.ConsentService")
    def test_passes_browser_fingerprint(self, MockConsentService, mock_db):
        consent_log = _make_consent_log()
        mock_service = MagicMock()
        mock_service.record_consent.return_value = consent_log
        MockConsentService.return_value = mock_service

        request_data = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Pro",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            browser_fingerprint="abc123def456",
        )
        http_request = _make_http_request()

        with patch("app.routers.consent.ConsentRecordResponse") as MockResponse:
            MockResponse.model_validate.return_value = MagicMock()
            record_consent(
                user_id="user_1",
                request_data=request_data,
                http_request=http_request,
                db=mock_db,
            )

        call_kwargs = mock_service.record_consent.call_args.kwargs
        assert call_kwargs["browser_fingerprint"] == "abc123def456"


# ---------------------------------------------------------------------------
# get_consent_history
# ---------------------------------------------------------------------------


class TestGetConsentHistory:
    """Tests for GET /consent/{user_id}/history."""

    @patch("app.routers.consent.ConsentService")
    def test_returns_user_history(self, MockConsentService, mock_db):
        log1 = _make_consent_log(id=1)
        log2 = _make_consent_log(id=2)

        mock_service = MagicMock()
        mock_service.get_user_consent_history.return_value = [log1, log2]
        MockConsentService.return_value = mock_service

        with patch("app.routers.consent.ConsentHistoryResponse") as MockResponse:
            MockResponse.model_validate.side_effect = lambda log: MagicMock(id=log.id)
            result = get_consent_history(user_id="user_1", db=mock_db)

        assert len(result) == 2
        mock_service.get_user_consent_history.assert_called_once_with("user_1")

    @patch("app.routers.consent.ConsentService")
    def test_returns_empty_for_unknown_user(self, MockConsentService, mock_db):
        mock_service = MagicMock()
        mock_service.get_user_consent_history.return_value = []
        MockConsentService.return_value = mock_service

        result = get_consent_history(user_id="user_unknown", db=mock_db)

        assert len(result) == 0


# ---------------------------------------------------------------------------
# get_current_consent_version
# ---------------------------------------------------------------------------


class TestGetCurrentConsentVersion:
    """Tests for GET /consent/current-version."""

    @patch("app.routers.consent.ConsentService")
    def test_returns_version_and_languages(self, MockConsentService):
        MockConsentService.get_current_consent_version.return_value = "v1.0.0"
        MockConsentService.get_supported_languages.return_value = ["en", "uk"]

        result = get_current_consent_version()

        assert result.version == "v1.0.0"
        assert result.supported_languages == ["en", "uk"]

    @patch("app.routers.consent.ConsentService")
    def test_response_shape(self, MockConsentService):
        MockConsentService.get_current_consent_version.return_value = "v2.0.0"
        MockConsentService.get_supported_languages.return_value = ["en"]

        result = get_current_consent_version()

        assert hasattr(result, "version")
        assert hasattr(result, "supported_languages")
        assert isinstance(result.supported_languages, list)
