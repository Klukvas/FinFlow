"""Tests for public plans router endpoints."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.routers.plans import list_plans, list_plans_with_features


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(
    id: int = 1,
    code: str = "professional",
    name: str = "Professional",
    period_days: int = 30,
    is_active: bool = True,
    version: int = 1,
):
    plan = MagicMock()
    plan.id = id
    plan.code = code
    plan.name = name
    plan.period_days = period_days
    plan.is_active = is_active
    plan.version = version
    return plan


def _make_plan_feature(feature_code: str, enabled: bool = True, limit_value: int | None = 5):
    pf = MagicMock()
    pf.feature_code = feature_code
    pf.enabled = enabled
    pf.limit_value = limit_value
    return pf


def _make_feature(code: str, name: str = "Feature"):
    feat = MagicMock()
    feat.code = code
    feat.name = name
    return feat


# ---------------------------------------------------------------------------
# list_plans
# ---------------------------------------------------------------------------


class TestListPlans:
    """Tests for GET /plans."""

    @patch("app.routers.plans.PlanRepository")
    def test_returns_active_plans(self, MockPlanRepo, mock_db):
        plan1 = _make_plan(id=1, code="basic", name="Basic")
        plan2 = _make_plan(id=2, code="professional", name="Professional")

        mock_repo = MagicMock()
        mock_repo.list_active.return_value = [plan1, plan2]
        MockPlanRepo.return_value = mock_repo

        with patch("app.routers.plans.PlanOut") as MockPlanOut:
            MockPlanOut.model_validate.side_effect = lambda p, **kw: MagicMock(
                code=p.code, name=p.name
            )
            result = list_plans(db=mock_db)

        assert len(result) == 2
        MockPlanRepo.assert_called_once_with(mock_db)

    @patch("app.routers.plans.PlanRepository")
    def test_returns_empty_when_no_active_plans(self, MockPlanRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.list_active.return_value = []
        MockPlanRepo.return_value = mock_repo

        with patch("app.routers.plans.PlanOut"):
            result = list_plans(db=mock_db)

        assert len(result) == 0


# ---------------------------------------------------------------------------
# list_plans_with_features
# ---------------------------------------------------------------------------


class TestListPlansWithFeatures:
    """Tests for GET /plans/with-features."""

    @patch("app.routers.plans.PlanRepository")
    def test_returns_plans_with_features(self, MockPlanRepo, mock_db):
        plan = _make_plan(id=1, code="professional", name="Professional")

        mock_repo = MagicMock()
        mock_repo.list_active.return_value = [plan]
        MockPlanRepo.return_value = mock_repo

        pf = _make_plan_feature("accounts", enabled=True, limit_value=10)
        feat = _make_feature("accounts", name="Accounts")

        # db.query(PlanFeature, Feature).join(...).filter(...).all()
        query = MagicMock()
        query.join.return_value.filter.return_value.all.return_value = [(pf, feat)]
        mock_db.query.return_value = query

        result = list_plans_with_features(db=mock_db)

        assert len(result) == 1
        assert result[0].code == "professional"
        assert "accounts" in result[0].features
        assert result[0].features["accounts"].limit_value == 10
        assert result[0].features["accounts"].enabled is True

    @patch("app.routers.plans.PlanRepository")
    def test_returns_empty_when_no_plans(self, MockPlanRepo, mock_db):
        mock_repo = MagicMock()
        mock_repo.list_active.return_value = []
        MockPlanRepo.return_value = mock_repo

        result = list_plans_with_features(db=mock_db)

        assert len(result) == 0

    @patch("app.routers.plans.PlanRepository")
    def test_plan_with_no_features(self, MockPlanRepo, mock_db):
        plan = _make_plan(id=1, code="basic", name="Basic")

        mock_repo = MagicMock()
        mock_repo.list_active.return_value = [plan]
        MockPlanRepo.return_value = mock_repo

        query = MagicMock()
        query.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value = query

        result = list_plans_with_features(db=mock_db)

        assert len(result) == 1
        assert result[0].code == "basic"
        assert result[0].features == {}

    @patch("app.routers.plans.PlanRepository")
    def test_plan_with_multiple_features(self, MockPlanRepo, mock_db):
        plan = _make_plan(id=1, code="professional")

        mock_repo = MagicMock()
        mock_repo.list_active.return_value = [plan]
        MockPlanRepo.return_value = mock_repo

        pf1 = _make_plan_feature("accounts", enabled=True, limit_value=20)
        feat1 = _make_feature("accounts", name="Accounts")
        pf2 = _make_plan_feature("categories", enabled=True, limit_value=50)
        feat2 = _make_feature("categories", name="Categories")
        pf3 = _make_plan_feature("pdf_parsing", enabled=False, limit_value=None)
        feat3 = _make_feature("pdf_parsing", name="PDF Parsing")

        query = MagicMock()
        query.join.return_value.filter.return_value.all.return_value = [
            (pf1, feat1), (pf2, feat2), (pf3, feat3)
        ]
        mock_db.query.return_value = query

        result = list_plans_with_features(db=mock_db)

        assert len(result[0].features) == 3
        assert result[0].features["accounts"].limit_value == 20
        assert result[0].features["categories"].limit_value == 50
        assert result[0].features["pdf_parsing"].enabled is False

    @patch("app.routers.plans.PlanRepository")
    def test_multiple_plans_each_with_features(self, MockPlanRepo, mock_db):
        basic = _make_plan(id=1, code="basic")
        pro = _make_plan(id=2, code="professional")

        mock_repo = MagicMock()
        mock_repo.list_active.return_value = [basic, pro]
        MockPlanRepo.return_value = mock_repo

        # Basic plan features
        basic_pf = _make_plan_feature("accounts", enabled=True, limit_value=3)
        basic_feat = _make_feature("accounts", name="Accounts")

        # Pro plan features
        pro_pf = _make_plan_feature("accounts", enabled=True, limit_value=20)
        pro_feat = _make_feature("accounts", name="Accounts")

        # db.query called per plan
        basic_query = MagicMock()
        basic_query.join.return_value.filter.return_value.all.return_value = [(basic_pf, basic_feat)]
        pro_query = MagicMock()
        pro_query.join.return_value.filter.return_value.all.return_value = [(pro_pf, pro_feat)]

        mock_db.query.side_effect = [basic_query, pro_query]

        result = list_plans_with_features(db=mock_db)

        assert len(result) == 2
        assert result[0].code == "basic"
        assert result[0].features["accounts"].limit_value == 3
        assert result[1].code == "professional"
        assert result[1].features["accounts"].limit_value == 20
