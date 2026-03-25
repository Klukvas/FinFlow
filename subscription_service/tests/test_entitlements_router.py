"""Tests for entitlements router endpoints."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.routers.entitlements import get_entitlements


# ---------------------------------------------------------------------------
# get_entitlements
# ---------------------------------------------------------------------------


class TestGetEntitlements:
    """Tests for GET /entitlements/{user_id}."""

    @patch("app.routers.entitlements.EntitlementsService")
    @patch("app.routers.entitlements.SubscriptionRepository")
    def test_returns_entitlements_for_user(self, MockSubRepo, MockEntService, mock_db):
        """Must return user entitlements with plan code and version."""
        mock_service = MagicMock()
        mock_service.get_entitlements.return_value = (
            "professional",
            2,
            {"accounts": {"enabled": True, "limit_value": 20}},
        )
        MockEntService.return_value = mock_service

        result = get_entitlements(user_id="user_1", db=mock_db)

        assert result.user_id == "user_1"
        assert result.plan_code == "professional"
        assert result.version == 2
        assert "accounts" in result.entitlements
        assert result.entitlements["accounts"]["limit_value"] == 20

    @patch("app.routers.entitlements.EntitlementsService")
    @patch("app.routers.entitlements.SubscriptionRepository")
    def test_returns_free_for_no_subscription(self, MockSubRepo, MockEntService, mock_db):
        """Must return 'free' plan with empty entitlements when user has no subscription."""
        mock_service = MagicMock()
        mock_service.get_entitlements.return_value = ("free", 1, {})
        MockEntService.return_value = mock_service

        result = get_entitlements(user_id="user_no_sub", db=mock_db)

        assert result.user_id == "user_no_sub"
        assert result.plan_code == "free"
        assert result.version == 1
        assert result.entitlements == {}

    @patch("app.routers.entitlements.EntitlementsService")
    @patch("app.routers.entitlements.SubscriptionRepository")
    def test_returns_multiple_features(self, MockSubRepo, MockEntService, mock_db):
        """Must handle multiple feature entitlements."""
        mock_service = MagicMock()
        mock_service.get_entitlements.return_value = (
            "professional",
            3,
            {
                "accounts": {"enabled": True, "limit_value": 20},
                "categories": {"enabled": True, "limit_value": 50},
                "pdf_parsing": {"enabled": True, "limit_value": None},
            },
        )
        MockEntService.return_value = mock_service

        result = get_entitlements(user_id="user_pro", db=mock_db)

        assert result.plan_code == "professional"
        assert len(result.entitlements) == 3
        assert result.entitlements["pdf_parsing"]["limit_value"] is None

    @patch("app.routers.entitlements.EntitlementsService")
    @patch("app.routers.entitlements.SubscriptionRepository")
    def test_passes_correct_user_id_to_service(self, MockSubRepo, MockEntService, mock_db):
        """Must pass user_id from path parameter to EntitlementsService."""
        mock_service = MagicMock()
        mock_service.get_entitlements.return_value = ("free", 1, {})
        MockEntService.return_value = mock_service

        get_entitlements(user_id="specific_user_42", db=mock_db)

        mock_service.get_entitlements.assert_called_once_with("specific_user_42")

    @patch("app.routers.entitlements.EntitlementsService")
    @patch("app.routers.entitlements.SubscriptionRepository")
    def test_creates_repo_and_service_with_db(self, MockSubRepo, MockEntService, mock_db):
        """Must create SubscriptionRepository with db, then pass to EntitlementsService."""
        mock_repo_instance = MagicMock()
        MockSubRepo.return_value = mock_repo_instance

        mock_service = MagicMock()
        mock_service.get_entitlements.return_value = ("free", 1, {})
        MockEntService.return_value = mock_service

        get_entitlements(user_id="user_1", db=mock_db)

        MockSubRepo.assert_called_once_with(mock_db)
        MockEntService.assert_called_once_with(mock_repo_instance)
