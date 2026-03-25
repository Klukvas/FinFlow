"""Tests for admin plan management router endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.routers.admin_plans import (
    list_all_plans,
    get_plan,
    create_plan,
    update_plan,
    update_plan_features,
    list_all_features,
    plan_to_admin_out,
)
from app.schemas.admin import PlanCreate, PlanUpdate, PlanFeaturesUpdate, PlanFeatureIn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan_model(
    id: int = 1,
    code: str = "professional",
    name: str = "Professional",
    period_days: int = 30,
    is_active: bool = True,
    version: int = 1,
    features: list | None = None,
):
    plan = MagicMock()
    plan.id = id
    plan.code = code
    plan.name = name
    plan.period_days = period_days
    plan.is_active = is_active
    plan.version = version
    plan.features = features or []
    plan.created_at = datetime.utcnow()
    plan.updated_at = datetime.utcnow()
    return plan


def _make_feature_model(code: str = "accounts", name: str = "Accounts", description: str | None = None):
    feat = MagicMock()
    feat.code = code
    feat.name = name
    feat.description = description
    return feat


def _make_plan_feature_model(
    feature_code: str = "accounts",
    enabled: bool = True,
    limit_value: int | None = 5,
):
    pf = MagicMock()
    pf.feature_code = feature_code
    pf.enabled = enabled
    pf.limit_value = limit_value
    return pf


# ---------------------------------------------------------------------------
# plan_to_admin_out helper
# ---------------------------------------------------------------------------


class TestPlanToAdminOut:
    """Tests for the plan_to_admin_out conversion helper."""

    def test_converts_plan_without_features(self):
        plan = _make_plan_model(features=[])
        result = plan_to_admin_out(plan)
        assert result.id == plan.id
        assert result.code == "professional"
        assert result.features == []

    def test_converts_plan_with_features(self):
        pf = _make_plan_feature_model(feature_code="accounts", enabled=True, limit_value=10)
        plan = _make_plan_model(features=[pf])

        result = plan_to_admin_out(plan)

        assert len(result.features) == 1
        assert result.features[0].feature_code == "accounts"
        assert result.features[0].limit_value == 10


# ---------------------------------------------------------------------------
# list_all_plans
# ---------------------------------------------------------------------------


class TestListAllPlans:
    """Tests for GET /admin/plans."""

    def test_returns_all_plans(self, mock_db):
        plan1 = _make_plan_model(id=1, code="basic")
        plan2 = _make_plan_model(id=2, code="professional")

        query_mock = MagicMock()
        query_mock.order_by.return_value.all.return_value = [plan1, plan2]
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = list_all_plans(admin=admin, db=mock_db)

        assert len(result.items) == 2
        assert result.items[0].code == "basic"
        assert result.items[1].code == "professional"

    def test_returns_empty_list(self, mock_db):
        query_mock = MagicMock()
        query_mock.order_by.return_value.all.return_value = []
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = list_all_plans(admin=admin, db=mock_db)

        assert len(result.items) == 0


# ---------------------------------------------------------------------------
# get_plan
# ---------------------------------------------------------------------------


class TestGetPlan:
    """Tests for GET /admin/plans/{plan_id}."""

    def test_returns_plan_by_id(self, mock_db):
        plan = _make_plan_model(id=42, code="enterprise")

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = get_plan(plan_id=42, admin=admin, db=mock_db)

        assert result.id == 42
        assert result.code == "enterprise"

    def test_plan_not_found_raises_404(self, mock_db):
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}

        with pytest.raises(HTTPException) as exc_info:
            get_plan(plan_id=999, admin=admin, db=mock_db)

        assert exc_info.value.status_code == 404
        assert "Plan not found" in exc_info.value.detail


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------


class TestCreatePlan:
    """Tests for POST /admin/plans."""

    def test_creates_new_plan(self, mock_db):
        data = PlanCreate(code="premium", name="Premium", period_days=30)

        # No existing plan with that code
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        mock_db.query.return_value = query_mock

        # After db.refresh, the plan gets an id
        def refresh_side_effect(obj):
            obj.id = 10
            obj.version = 1
            obj.features = []
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()

        mock_db.refresh.side_effect = refresh_side_effect

        admin = {"sub": "admin_1"}
        result = create_plan(data=data, admin=admin, db=mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.code == "premium"

    def test_duplicate_code_raises_400(self, mock_db):
        data = PlanCreate(code="basic", name="Basic", period_days=30)

        existing_plan = _make_plan_model(code="basic")
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = existing_plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}

        with pytest.raises(HTTPException) as exc_info:
            create_plan(data=data, admin=admin, db=mock_db)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


# ---------------------------------------------------------------------------
# update_plan
# ---------------------------------------------------------------------------


class TestUpdatePlan:
    """Tests for PATCH /admin/plans/{plan_id}."""

    def test_updates_name(self, mock_db):
        plan = _make_plan_model(id=1, code="basic", name="Basic", version=1)
        data = PlanUpdate(name="Basic Plus")

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = update_plan(plan_id=1, data=data, admin=admin, db=mock_db)

        assert plan.name == "Basic Plus"
        assert plan.version == 2
        mock_db.commit.assert_called_once()

    def test_updates_period_days(self, mock_db):
        plan = _make_plan_model(id=1, version=1)
        data = PlanUpdate(period_days=60)

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        update_plan(plan_id=1, data=data, admin=admin, db=mock_db)

        assert plan.period_days == 60
        assert plan.version == 2

    def test_updates_is_active(self, mock_db):
        plan = _make_plan_model(id=1, is_active=True, version=1)
        data = PlanUpdate(is_active=False)

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        update_plan(plan_id=1, data=data, admin=admin, db=mock_db)

        assert plan.is_active is False

    def test_no_update_fields_still_increments_version(self, mock_db):
        plan = _make_plan_model(id=1, version=3)
        data = PlanUpdate()  # All None

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = plan
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        update_plan(plan_id=1, data=data, admin=admin, db=mock_db)

        assert plan.version == 4

    def test_plan_not_found_raises_404(self, mock_db):
        data = PlanUpdate(name="New Name")

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}

        with pytest.raises(HTTPException) as exc_info:
            update_plan(plan_id=999, data=data, admin=admin, db=mock_db)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# update_plan_features
# ---------------------------------------------------------------------------


class TestUpdatePlanFeatures:
    """Tests for PATCH /admin/plans/{plan_id}/features."""

    def test_updates_features_successfully(self, mock_db):
        plan = _make_plan_model(id=1, version=1)

        # First query: find plan by id
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        # Second query: validate feature codes
        feat1 = _make_feature_model(code="accounts")
        feat2 = _make_feature_model(code="categories")
        feature_query = MagicMock()
        feature_query.filter.return_value.all.return_value = [feat1, feat2]

        # Third query: delete existing plan features
        delete_query = MagicMock()
        delete_query.filter.return_value.delete.return_value = 2

        mock_db.query.side_effect = [plan_query, feature_query, delete_query]

        data = PlanFeaturesUpdate(features=[
            PlanFeatureIn(feature_code="accounts", enabled=True, limit_value=10),
            PlanFeatureIn(feature_code="categories", enabled=True, limit_value=20),
        ])

        admin = {"sub": "admin_1"}
        update_plan_features(plan_id=1, data=data, admin=admin, db=mock_db)

        assert plan.version == 2
        mock_db.commit.assert_called_once()
        # Two new PlanFeature objects added
        assert mock_db.add.call_count == 2

    def test_invalid_feature_code_raises_400(self, mock_db):
        plan = _make_plan_model(id=1)

        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        # Feature "nonexistent" not found in DB
        feat1 = _make_feature_model(code="accounts")
        feature_query = MagicMock()
        feature_query.filter.return_value.all.return_value = [feat1]

        mock_db.query.side_effect = [plan_query, feature_query]

        data = PlanFeaturesUpdate(features=[
            PlanFeatureIn(feature_code="accounts", enabled=True),
            PlanFeatureIn(feature_code="nonexistent", enabled=True),
        ])

        admin = {"sub": "admin_1"}

        with pytest.raises(HTTPException) as exc_info:
            update_plan_features(plan_id=1, data=data, admin=admin, db=mock_db)

        assert exc_info.value.status_code == 400
        assert "Invalid feature codes" in exc_info.value.detail

    def test_plan_not_found_raises_404(self, mock_db):
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = plan_query

        data = PlanFeaturesUpdate(features=[
            PlanFeatureIn(feature_code="accounts", enabled=True),
        ])

        admin = {"sub": "admin_1"}

        with pytest.raises(HTTPException) as exc_info:
            update_plan_features(plan_id=999, data=data, admin=admin, db=mock_db)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# list_all_features
# ---------------------------------------------------------------------------


class TestListAllFeatures:
    """Tests for GET /admin/features."""

    def test_returns_all_features(self, mock_db, make_feature):
        feat1 = make_feature(code="accounts", name="Accounts")
        feat2 = make_feature(code="categories", name="Categories")

        query_mock = MagicMock()
        query_mock.order_by.return_value.all.return_value = [feat1, feat2]
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = list_all_features(admin=admin, db=mock_db)

        assert len(result.items) == 2

    def test_returns_empty_list(self, mock_db):
        query_mock = MagicMock()
        query_mock.order_by.return_value.all.return_value = []
        mock_db.query.return_value = query_mock

        admin = {"sub": "admin_1"}
        result = list_all_features(admin=admin, db=mock_db)

        assert len(result.items) == 0
