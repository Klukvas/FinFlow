"""Tests for features router endpoints."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.routers.features import (
    list_features,
    get_plan_features,
    get_user_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feature(code: str = "accounts", name: str = "Accounts", description: str | None = None):
    feat = MagicMock()
    feat.code = code
    feat.name = name
    feat.description = description
    return feat


def _make_plan_feature(feature_code: str = "accounts", enabled: bool = True, limit_value: int | None = 5):
    pf = MagicMock()
    pf.feature_code = feature_code
    pf.enabled = enabled
    pf.limit_value = limit_value
    return pf


# ---------------------------------------------------------------------------
# list_features
# ---------------------------------------------------------------------------


class TestListFeatures:
    """Tests for GET /features."""

    @patch("app.routers.features.FeatureRepository")
    def test_returns_all_features(self, MockFeatureRepo, mock_db):
        feat1 = _make_feature(code="accounts", name="Accounts")
        feat2 = _make_feature(code="categories", name="Categories")

        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [feat1, feat2]
        MockFeatureRepo.return_value = mock_repo

        with patch("app.routers.features.FeatureOut") as MockFeatureOut:
            MockFeatureOut.model_validate.side_effect = lambda f, **kw: MagicMock(
                code=f.code, name=f.name
            )
            result = list_features(db=mock_db)

        assert len(result) == 2
        MockFeatureRepo.assert_called_once_with(mock_db)

    @patch("app.routers.features.FeatureRepository")
    def test_returns_empty_list(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = []
        MockFeatureRepo.return_value = mock_repo

        with patch("app.routers.features.FeatureOut") as MockFeatureOut:
            result = list_features(db=mock_db)

        assert len(result) == 0


# ---------------------------------------------------------------------------
# get_plan_features
# ---------------------------------------------------------------------------


class TestGetPlanFeatures:
    """Tests for GET /plans/{plan_code}/features."""

    @patch("app.routers.features.FeatureRepository")
    def test_returns_plan_features(self, MockFeatureRepo, mock_db):
        pf1 = _make_plan_feature(feature_code="accounts", enabled=True, limit_value=5)
        pf2 = _make_plan_feature(feature_code="categories", enabled=True, limit_value=20)

        mock_repo = MagicMock()
        mock_repo.get_plan_features.return_value = [pf1, pf2]
        MockFeatureRepo.return_value = mock_repo

        with patch("app.routers.features.PlanFeatureOut") as MockPFOut:
            MockPFOut.model_validate.side_effect = lambda pf, **kw: MagicMock(
                feature_code=pf.feature_code
            )
            result = get_plan_features(plan_code="professional", db=mock_db)

        assert len(result) == 2
        mock_repo.get_plan_features.assert_called_once_with("professional")

    @patch("app.routers.features.FeatureRepository")
    def test_returns_empty_for_unknown_plan(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.get_plan_features.return_value = []
        MockFeatureRepo.return_value = mock_repo

        with patch("app.routers.features.PlanFeatureOut"):
            result = get_plan_features(plan_code="nonexistent", db=mock_db)

        assert len(result) == 0


# ---------------------------------------------------------------------------
# get_user_features
# ---------------------------------------------------------------------------


class TestGetUserFeatures:
    """Tests for GET /features/{user_id}."""

    @patch("app.routers.features.FeatureRepository")
    def test_returns_user_features(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.get_user_features.return_value = [
            {"feature_code": "accounts", "enabled": True, "limit_value": 10, "plan_code": "professional"},
            {"feature_code": "categories", "enabled": True, "limit_value": 50, "plan_code": "professional"},
        ]
        MockFeatureRepo.return_value = mock_repo

        result = get_user_features(user_id="user_1", db=mock_db)

        assert len(result) == 2
        assert result[0].feature_code == "accounts"
        assert result[0].plan_code == "professional"
        assert result[1].feature_code == "categories"

    @patch("app.routers.features.FeatureRepository")
    def test_returns_empty_for_no_subscription(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.get_user_features.return_value = []
        MockFeatureRepo.return_value = mock_repo

        result = get_user_features(user_id="user_no_sub", db=mock_db)

        assert len(result) == 0

    @patch("app.routers.features.FeatureRepository")
    def test_passes_user_id_to_repository(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.get_user_features.return_value = []
        MockFeatureRepo.return_value = mock_repo

        get_user_features(user_id="specific_user", db=mock_db)

        mock_repo.get_user_features.assert_called_once_with("specific_user")

    @patch("app.routers.features.FeatureRepository")
    def test_feature_with_null_limit(self, MockFeatureRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.get_user_features.return_value = [
            {"feature_code": "pdf_parsing", "enabled": True, "limit_value": None, "plan_code": "professional"},
        ]
        MockFeatureRepo.return_value = mock_repo

        result = get_user_features(user_id="user_1", db=mock_db)

        assert len(result) == 1
        assert result[0].limit_value is None
