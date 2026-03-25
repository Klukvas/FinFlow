"""Tests for admin-specific Pydantic schemas."""

from __future__ import annotations

import pytest
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError

from app.schemas.admin import (
    PlanFeatureIn,
    PlanCreate,
    PlanUpdate,
    PlanFeaturesUpdate,
    PlanFeatureOut,
    AdminPlanOut,
    AdminPlansListResponse,
    FeatureOut,
    AdminFeaturesListResponse,
    AdminSubscriptionOut,
    AdminSubscriptionsListResponse,
    SubscriptionStatsOut,
)


# ======================================================================
# PlanFeatureIn
# ======================================================================


class TestPlanFeatureIn:
    def test_valid_minimal(self):
        schema = PlanFeatureIn(feature_code="accounts")
        assert schema.feature_code == "accounts"
        assert schema.enabled is True
        assert schema.limit_value is None

    def test_valid_with_all_fields(self):
        schema = PlanFeatureIn(feature_code="accounts", enabled=False, limit_value=10)
        assert schema.enabled is False
        assert schema.limit_value == 10

    def test_missing_feature_code_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanFeatureIn()


# ======================================================================
# PlanCreate
# ======================================================================


class TestPlanCreate:
    def test_valid_minimal(self):
        schema = PlanCreate(code="basic", name="Basic Plan", period_days=30)
        assert schema.code == "basic"
        assert schema.is_active is True

    def test_valid_inactive(self):
        schema = PlanCreate(code="legacy_plan", name="Legacy", period_days=365, is_active=False)
        assert schema.is_active is False

    def test_code_must_start_with_lowercase(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="BasicPlan", name="Basic", period_days=30)

    def test_code_no_hyphens(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic-plan", name="Basic", period_days=30)

    def test_code_allows_digits_and_underscores(self):
        schema = PlanCreate(code="plan_v2_pro", name="Plan V2 Pro", period_days=30)
        assert schema.code == "plan_v2_pro"

    def test_empty_code_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="", name="Basic", period_days=30)

    def test_code_too_long_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="a" * 65, name="Basic", period_days=30)

    def test_empty_name_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="", period_days=30)

    def test_name_too_long_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="x" * 256, period_days=30)

    def test_period_days_zero_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="Basic", period_days=0)

    def test_period_days_negative_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="Basic", period_days=-1)

    def test_missing_required_fields_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate()


# ======================================================================
# PlanUpdate
# ======================================================================


class TestPlanUpdate:
    def test_all_fields_optional(self):
        schema = PlanUpdate()
        assert schema.name is None
        assert schema.period_days is None
        assert schema.is_active is None

    def test_partial_name_only(self):
        schema = PlanUpdate(name="New Name")
        assert schema.name == "New Name"
        assert schema.period_days is None

    def test_partial_period_days_only(self):
        schema = PlanUpdate(period_days=90)
        assert schema.period_days == 90

    def test_partial_is_active_only(self):
        schema = PlanUpdate(is_active=False)
        assert schema.is_active is False

    def test_full_update(self):
        schema = PlanUpdate(name="Updated", period_days=60, is_active=True)
        assert schema.name == "Updated"
        assert schema.period_days == 60
        assert schema.is_active is True

    def test_empty_name_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanUpdate(name="")

    def test_period_days_zero_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanUpdate(period_days=0)


# ======================================================================
# PlanFeaturesUpdate
# ======================================================================


class TestPlanFeaturesUpdate:
    def test_valid_single_feature(self):
        schema = PlanFeaturesUpdate(
            features=[PlanFeatureIn(feature_code="accounts", enabled=True, limit_value=5)]
        )
        assert len(schema.features) == 1

    def test_valid_multiple_features(self):
        schema = PlanFeaturesUpdate(
            features=[
                PlanFeatureIn(feature_code="accounts", enabled=True, limit_value=5),
                PlanFeatureIn(feature_code="categories", enabled=False),
            ]
        )
        assert len(schema.features) == 2

    def test_empty_features_list(self):
        schema = PlanFeaturesUpdate(features=[])
        assert len(schema.features) == 0

    def test_missing_features_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanFeaturesUpdate()


# ======================================================================
# PlanFeatureOut
# ======================================================================


class TestPlanFeatureOut:
    def test_valid(self):
        schema = PlanFeatureOut(feature_code="accounts", enabled=True, limit_value=10)
        assert schema.feature_code == "accounts"
        assert schema.enabled is True
        assert schema.limit_value == 10

    def test_without_limit(self):
        schema = PlanFeatureOut(feature_code="pdf_parsing", enabled=True)
        assert schema.limit_value is None


# ======================================================================
# AdminPlanOut
# ======================================================================


class TestAdminPlanOut:
    def test_valid_without_features(self):
        now = datetime.utcnow()
        schema = AdminPlanOut(
            id=1,
            code="basic",
            name="Basic",
            period_days=30,
            is_active=True,
            version=1,
            created_at=now,
            updated_at=now,
        )
        assert schema.features == []

    def test_valid_with_features(self):
        now = datetime.utcnow()
        schema = AdminPlanOut(
            id=1,
            code="professional",
            name="Professional",
            period_days=30,
            is_active=True,
            version=2,
            created_at=now,
            updated_at=now,
            features=[
                PlanFeatureOut(feature_code="accounts", enabled=True, limit_value=20),
            ],
        )
        assert len(schema.features) == 1
        assert schema.features[0].feature_code == "accounts"


# ======================================================================
# AdminPlansListResponse
# ======================================================================


class TestAdminPlansListResponse:
    def test_valid_empty(self):
        schema = AdminPlansListResponse(items=[])
        assert len(schema.items) == 0

    def test_valid_with_items(self):
        now = datetime.utcnow()
        plan = AdminPlanOut(
            id=1, code="basic", name="Basic", period_days=30,
            is_active=True, version=1, created_at=now, updated_at=now,
        )
        schema = AdminPlansListResponse(items=[plan])
        assert len(schema.items) == 1


# ======================================================================
# FeatureOut
# ======================================================================


class TestFeatureOut:
    def test_valid_without_description(self):
        schema = FeatureOut(code="accounts", name="Accounts")
        assert schema.description is None

    def test_valid_with_description(self):
        schema = FeatureOut(code="accounts", name="Accounts", description="Manage accounts")
        assert schema.description == "Manage accounts"


# ======================================================================
# AdminFeaturesListResponse
# ======================================================================


class TestAdminFeaturesListResponse:
    def test_valid_empty(self):
        schema = AdminFeaturesListResponse(items=[])
        assert len(schema.items) == 0

    def test_valid_with_items(self):
        schema = AdminFeaturesListResponse(
            items=[FeatureOut(code="accounts", name="Accounts")]
        )
        assert len(schema.items) == 1


# ======================================================================
# AdminSubscriptionOut
# ======================================================================


class TestAdminSubscriptionOut:
    def test_valid_minimal(self):
        now = datetime.utcnow()
        schema = AdminSubscriptionOut(
            id=1,
            user_id="user_1",
            plan_code="professional",
            status="active",
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        assert schema.expires_at is None
        assert schema.canceled_at is None
        assert schema.payment_provider is None
        assert schema.paddle_customer_id is None
        assert schema.cancellation_reason is None

    def test_valid_full(self):
        now = datetime.utcnow()
        schema = AdminSubscriptionOut(
            id=1,
            user_id="user_1",
            plan_code="professional",
            status="canceled",
            started_at=now,
            expires_at=now,
            canceled_at=now,
            auto_renew=False,
            payment_provider="PADDLE",
            last_payment_id="pay_001",
            next_billing_date=now,
            paddle_customer_id="ctm_123",
            paddle_subscription_id="sub_456",
            paddle_price_id="pri_789",
            cancellation_reason="too_expensive",
            cancellation_comment="Found cheaper option",
            created_at=now,
            updated_at=now,
        )
        assert schema.auto_renew is False
        assert schema.cancellation_reason == "too_expensive"


# ======================================================================
# AdminSubscriptionsListResponse
# ======================================================================


class TestAdminSubscriptionsListResponse:
    def test_valid_empty(self):
        schema = AdminSubscriptionsListResponse(
            items=[], total=0, page=1, page_size=20, total_pages=1,
        )
        assert schema.total == 0
        assert schema.total_pages == 1

    def test_valid_with_pagination(self):
        now = datetime.utcnow()
        sub = AdminSubscriptionOut(
            id=1, user_id="u1", plan_code="basic", status="active",
            started_at=now, created_at=now, updated_at=now,
        )
        schema = AdminSubscriptionsListResponse(
            items=[sub], total=50, page=3, page_size=20, total_pages=3,
        )
        assert schema.total == 50
        assert schema.page == 3
        assert len(schema.items) == 1


# ======================================================================
# SubscriptionStatsOut
# ======================================================================


class TestSubscriptionStatsOut:
    def test_valid(self):
        schema = SubscriptionStatsOut(
            total=100, active=80, past_due=10, canceled=8, paused=2,
        )
        assert schema.total == 100
        assert schema.active == 80
        assert schema.past_due == 10

    def test_all_zeros(self):
        schema = SubscriptionStatsOut(
            total=0, active=0, past_due=0, canceled=0, paused=0,
        )
        assert schema.total == 0
