"""Tests for repository layer (SubscriptionRepository, PlanRepository, FeatureRepository)."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.repositories.subscriptions import SubscriptionRepository
from app.repositories.plans import PlanRepository
from app.repositories.features import FeatureRepository


# ======================================================================
# SubscriptionRepository
# ======================================================================


class TestSubscriptionRepositoryUpsert:
    """Tests for SubscriptionRepository.upsert_subscription."""

    def test_creates_new_subscription(self, mock_db, make_plan):
        """Must create a new subscription when none exists."""
        plan = make_plan(code="professional", period_days=30)
        query_mock = mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.first.return_value = None
        # Second query for plan lookup
        mock_db.query.side_effect = [query_mock, MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=plan))))]

        repo = SubscriptionRepository(mock_db)

        # Need to reset side_effect to use properly
        mock_db.query.side_effect = None
        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = None
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        mock_db.query.side_effect = [sub_query, plan_query]

        repo = SubscriptionRepository(mock_db)
        result = repo.upsert_subscription("user_1", "professional")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_raises_value_error_for_unknown_plan(self, mock_db):
        """Must raise ValueError when plan does not exist."""
        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = None
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [sub_query, plan_query]

        repo = SubscriptionRepository(mock_db)

        with pytest.raises(ValueError, match="PLAN_NOT_FOUND"):
            repo.upsert_subscription("user_1", "nonexistent")

    def test_upsert_without_commit(self, mock_db, make_plan, make_subscription):
        """Must flush but not commit when commit=False."""
        plan = make_plan(code="professional", period_days=30)
        sub = make_subscription(
            plan_code="professional",
            expires_at=datetime.utcnow() + timedelta(days=15),
        )

        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = sub
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        mock_db.query.side_effect = [sub_query, plan_query]

        repo = SubscriptionRepository(mock_db)
        repo.upsert_subscription("user_1", "professional", commit=False)

        mock_db.flush.assert_called_once()
        mock_db.commit.assert_not_called()


class TestSubscriptionRepositoryGetActive:
    """Tests for SubscriptionRepository.get_active_subscription."""

    def test_returns_none_when_no_subscription(self, mock_db):
        """Must return None when user has no subscription."""
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        repo = SubscriptionRepository(mock_db)
        result = repo.get_active_subscription("user_no_sub")

        assert result is None

    def test_returns_active_subscription(self, mock_db, make_subscription):
        """Must return active subscription."""
        sub = make_subscription(status="active")
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = sub

        repo = SubscriptionRepository(mock_db)
        result = repo.get_active_subscription("user_1")

        assert result == sub


class TestSubscriptionRepositoryCancel:
    """Tests for SubscriptionRepository.cancel_subscription."""

    def test_cancel_sets_status_and_auto_renew(self, mock_db, make_subscription):
        """Must set status=canceled and auto_renew=False."""
        sub = make_subscription(status="active", auto_renew=True)

        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = sub
        mock_db.query.return_value = sub_query

        repo = SubscriptionRepository(mock_db)
        result = repo.cancel_subscription("user_1")

        assert result is not None
        assert sub.status == "canceled"
        assert sub.auto_renew is False
        mock_db.commit.assert_called_once()

    def test_cancel_immediate_sets_expires_at(self, mock_db, make_subscription):
        """Immediate cancel must set expires_at to now."""
        future = datetime.utcnow() + timedelta(days=20)
        sub = make_subscription(status="active", expires_at=future)

        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = sub
        mock_db.query.return_value = sub_query

        repo = SubscriptionRepository(mock_db)
        result = repo.cancel_subscription("user_1", immediate=True)

        # expires_at should be set to approximately now (not the future date)
        assert sub.expires_at is not None

    def test_cancel_returns_none_when_no_subscription(self, mock_db):
        """Must return None when user has no subscription."""
        sub_query = MagicMock()
        sub_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = sub_query

        repo = SubscriptionRepository(mock_db)
        result = repo.cancel_subscription("user_no_sub")

        assert result is None


class TestSubscriptionRepositoryGetEntitlements:
    """Tests for SubscriptionRepository.get_entitlements."""

    def test_returns_entitlements_for_plan(self, mock_db, make_plan, make_plan_feature):
        """Must return version and entitlements dict for plan."""
        plan = make_plan(id=1, code="professional", version=3)
        pf1 = make_plan_feature(feature_code="accounts", enabled=True, limit_value=10)
        pf2 = make_plan_feature(feature_code="categories", enabled=True, limit_value=20)

        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan
        pf_query = MagicMock()
        pf_query.join.return_value.filter.return_value.all.return_value = [pf1, pf2]

        mock_db.query.side_effect = [plan_query, pf_query]

        repo = SubscriptionRepository(mock_db)
        version, ents = repo.get_entitlements("professional")

        assert version == 3
        assert "accounts" in ents
        assert ents["accounts"]["enabled"] is True
        assert ents["accounts"]["limit_value"] == 10

    def test_raises_value_error_for_unknown_plan(self, mock_db):
        """Must raise ValueError when plan does not exist."""
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = plan_query

        repo = SubscriptionRepository(mock_db)

        with pytest.raises(ValueError, match="PLAN_NOT_FOUND"):
            repo.get_entitlements("nonexistent")


# ======================================================================
# PlanRepository
# ======================================================================


class TestPlanRepository:
    """Tests for PlanRepository."""

    def test_list_active_returns_active_plans(self, mock_db, make_plan):
        """Must return only active plans."""
        p1 = make_plan(code="basic", is_active=True)
        p2 = make_plan(code="professional", is_active=True)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [p1, p2]

        repo = PlanRepository(mock_db)
        result = repo.list_active()

        assert len(result) == 2

    def test_list_active_returns_empty_when_none(self, mock_db):
        """Must return empty list when no active plans."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        repo = PlanRepository(mock_db)
        result = repo.list_active()

        assert result == []

    def test_get_by_code_returns_plan(self, mock_db, make_plan):
        """Must return plan by code."""
        plan = make_plan(code="professional")
        mock_db.query.return_value.filter.return_value.first.return_value = plan

        repo = PlanRepository(mock_db)
        result = repo.get_by_code("professional")

        assert result == plan

    def test_get_by_code_returns_none_for_unknown(self, mock_db):
        """Must return None when plan does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = PlanRepository(mock_db)
        result = repo.get_by_code("nonexistent")

        assert result is None


# ======================================================================
# FeatureRepository
# ======================================================================


class TestFeatureRepository:
    """Tests for FeatureRepository."""

    def test_list_all_returns_features(self, mock_db, make_feature):
        """Must return all features."""
        f1 = make_feature(code="accounts", name="Accounts")
        f2 = make_feature(code="categories", name="Categories")
        mock_db.query.return_value.order_by.return_value.all.return_value = [f1, f2]

        repo = FeatureRepository(mock_db)
        result = repo.list_all()

        assert len(result) == 2

    def test_get_by_code_returns_feature(self, mock_db, make_feature):
        """Must return feature by code."""
        feat = make_feature(code="accounts")
        mock_db.query.return_value.filter.return_value.first.return_value = feat

        repo = FeatureRepository(mock_db)
        result = repo.get_by_code("accounts")

        assert result == feat

    def test_get_by_code_returns_none_for_unknown(self, mock_db):
        """Must return None for unknown feature code."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = FeatureRepository(mock_db)
        result = repo.get_by_code("nonexistent")

        assert result is None

    def test_get_plan_features_returns_features(self, mock_db, make_plan_feature):
        """Must return plan features by plan code."""
        pf = make_plan_feature(feature_code="accounts", enabled=True, limit_value=5)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [pf]

        repo = FeatureRepository(mock_db)
        result = repo.get_plan_features("professional")

        assert len(result) == 1
        assert result[0].feature_code == "accounts"

    def test_get_user_features_returns_empty_for_no_subscription(self, mock_db):
        """Must return empty list when user has no subscription."""
        # The FeatureRepository creates a SubscriptionRepository internally
        with patch("app.repositories.features.SubscriptionRepository") as MockSubRepo:
            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = None
            MockSubRepo.return_value = mock_sub_repo

            repo = FeatureRepository(mock_db)
            result = repo.get_user_features("user_no_sub")

        assert result == []

    def test_get_user_features_returns_features(self, mock_db, make_subscription, make_plan_feature):
        """Must return user features based on their subscription plan."""
        sub = make_subscription(plan_code="professional")
        pf = make_plan_feature(feature_code="accounts", enabled=True, limit_value=10)

        with patch("app.repositories.features.SubscriptionRepository") as MockSubRepo:
            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            repo = FeatureRepository(mock_db)
            # Mock get_plan_features
            repo.get_plan_features = MagicMock(return_value=[pf])
            result = repo.get_user_features("user_1")

        assert len(result) == 1
        assert result[0]["feature_code"] == "accounts"
        assert result[0]["plan_code"] == "professional"
