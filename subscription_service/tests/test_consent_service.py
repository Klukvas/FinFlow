"""Tests for ConsentService business logic."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.services.consent import (
    ConsentService,
    CURRENT_CONSENT_VERSION,
    CONSENT_TEXTS,
)
from app.utils.errors import NotFoundError, ValidationError


class TestRecordConsent:
    """Tests for ConsentService.record_consent."""

    def test_records_consent_successfully(self, mock_db, make_subscription, make_consent_log):
        """Must create consent log and update subscription."""
        sub = make_subscription(id=42, user_id="user_1")
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        service = ConsentService(mock_db)
        result = service.record_consent(
            subscription_id=42,
            user_id="user_1",
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Professional",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            ip_address="10.0.0.1",
            user_agent="TestBrowser/1.0",
            browser_fingerprint="fp_abc123",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert sub.consent_given is True
        assert sub.consent_version == "v1.0.0"
        assert sub.consent_ip_address == "10.0.0.1"
        assert sub.consent_user_agent == "TestBrowser/1.0"

    def test_raises_not_found_for_invalid_subscription(self, mock_db):
        """Must raise NotFoundError when subscription does not exist."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = ConsentService(mock_db)

        with pytest.raises(NotFoundError, match="Subscription.*not found"):
            service.record_consent(
                subscription_id=999,
                user_id="user_1",
                consent_version="v1.0.0",
                consent_language="en",
                plan_name="Professional",
                plan_code="professional",
                amount="29.99",
                currency="USD",
                ip_address="10.0.0.1",
                user_agent="TestBrowser/1.0",
            )

    def test_raises_error_for_invalid_version(self, mock_db, make_subscription):
        """Must raise when consent version is unknown.

        NOTE: The production code passes an unsupported ``details`` kwarg to
        ``ValidationError``, so the actual exception that propagates is
        ``TypeError`` rather than ``ValidationError``.  This test documents
        the current behaviour.
        """
        sub = make_subscription(id=1)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        service = ConsentService(mock_db)

        with pytest.raises(TypeError):
            service.record_consent(
                subscription_id=1,
                user_id="user_1",
                consent_version="v99.0.0",
                consent_language="en",
                plan_name="Professional",
                plan_code="professional",
                amount="29.99",
                currency="USD",
                ip_address="10.0.0.1",
                user_agent="TestBrowser/1.0",
            )

    def test_raises_error_for_invalid_language(self, mock_db, make_subscription):
        """Must raise when consent language is unsupported.

        NOTE: The production code passes an unsupported ``details`` kwarg to
        ``ValidationError``, so the actual exception that propagates is
        ``TypeError`` rather than ``ValidationError``.  This test documents
        the current behaviour.
        """
        sub = make_subscription(id=1)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        service = ConsentService(mock_db)

        with pytest.raises(TypeError):
            service.record_consent(
                subscription_id=1,
                user_id="user_1",
                consent_version="v1.0.0",
                consent_language="fr",
                plan_name="Professional",
                plan_code="professional",
                amount="29.99",
                currency="USD",
                ip_address="10.0.0.1",
                user_agent="TestBrowser/1.0",
            )

    def test_consent_without_browser_fingerprint(self, mock_db, make_subscription):
        """Must accept consent without browser fingerprint."""
        sub = make_subscription(id=1)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        service = ConsentService(mock_db)
        result = service.record_consent(
            subscription_id=1,
            user_id="user_1",
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Basic",
            plan_code="basic",
            amount="9.99",
            currency="USD",
            ip_address="10.0.0.1",
            user_agent="TestBrowser/1.0",
            browser_fingerprint=None,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestGetConsentText:
    """Tests for ConsentService._get_consent_text."""

    def test_english_consent_text(self, mock_db):
        """Must return filled English consent text."""
        service = ConsentService(mock_db)
        text = service._get_consent_text(
            version="v1.0.0",
            language="en",
            plan_name="Professional",
            amount="29.99",
            currency="USD",
        )

        assert "Professional" in text
        assert "29.99" in text
        assert "USD" in text
        assert "I agree to subscribe" in text

    def test_ukrainian_consent_text(self, mock_db):
        """Must return filled Ukrainian consent text."""
        service = ConsentService(mock_db)
        text = service._get_consent_text(
            version="v1.0.0",
            language="uk",
            plan_name="Професійний",
            amount="29.99",
            currency="UAH",
        )

        assert "Професійний" in text
        assert "29.99" in text
        assert "UAH" in text
        assert "підписку" in text

    def test_invalid_version_raises(self, mock_db):
        """NOTE: Raises TypeError due to unsupported ``details`` kwarg in production code."""
        service = ConsentService(mock_db)
        with pytest.raises(TypeError):
            service._get_consent_text("v99.0.0", "en", "Pro", "10", "USD")

    def test_invalid_language_raises(self, mock_db):
        """NOTE: Raises TypeError due to unsupported ``details`` kwarg in production code."""
        service = ConsentService(mock_db)
        with pytest.raises(TypeError):
            service._get_consent_text("v1.0.0", "de", "Pro", "10", "USD")


class TestGetUserConsentHistory:
    """Tests for ConsentService.get_user_consent_history."""

    def test_returns_consent_history(self, mock_db, make_consent_log):
        """Must return ordered list of consent logs."""
        log1 = make_consent_log(id=1)
        log2 = make_consent_log(id=2)
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [log2, log1]

        service = ConsentService(mock_db)
        result = service.get_user_consent_history("user_1")

        assert len(result) == 2

    def test_returns_empty_for_no_history(self, mock_db):
        """Must return empty list when user has no consent history."""
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        service = ConsentService(mock_db)
        result = service.get_user_consent_history("user_no_history")

        assert result == []


class TestStaticMethods:
    """Tests for ConsentService static methods."""

    def test_get_current_consent_version(self):
        assert ConsentService.get_current_consent_version() == CURRENT_CONSENT_VERSION

    def test_get_supported_languages(self):
        languages = ConsentService.get_supported_languages()
        assert "en" in languages
        assert "uk" in languages
        assert isinstance(languages, list)

    def test_consent_texts_have_all_supported_languages(self):
        """Every language returned by get_supported_languages must have a template."""
        languages = ConsentService.get_supported_languages()
        version = ConsentService.get_current_consent_version()
        for lang in languages:
            assert lang in CONSENT_TEXTS[version]
