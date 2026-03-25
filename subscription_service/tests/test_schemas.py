"""Tests for Pydantic schemas (input validation)."""

from __future__ import annotations

import pytest
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError

from app.schemas.subscription import SetPlanIn, SubscriptionOut
from app.schemas.plan import PlanOut, PlanWithFeaturesOut, PlanFeatureOut
from app.schemas.entitlements import EntitlementsOut
from app.schemas.features import FeatureOut, UserFeatureOut
from app.schemas.features import PlanFeatureOut as FeaturesPlanFeatureOut
from app.schemas.cancellation import CancelSubscriptionRequest, CancelSubscriptionResponse
from app.schemas.consent import (
    ConsentRecordRequest,
    ConsentRecordResponse,
    ConsentHistoryResponse,
    ConsentVersionResponse,
)
from app.schemas.admin import (
    PlanCreate,
    PlanUpdate,
    PlanFeaturesUpdate,
    PlanFeatureIn,
    AdminPlanOut,
    AdminSubscriptionOut,
    AdminSubscriptionsListResponse,
    SubscriptionStatsOut,
)


# ======================================================================
# Subscription schemas
# ======================================================================


class TestSetPlanIn:
    def test_valid_minimal(self):
        schema = SetPlanIn(plan_code="basic")
        assert schema.plan_code == "basic"
        assert schema.status is None

    def test_valid_with_status(self):
        schema = SetPlanIn(plan_code="professional", status="active")
        assert schema.status == "active"

    def test_missing_plan_code_raises(self):
        with pytest.raises(PydanticValidationError):
            SetPlanIn()


class TestSubscriptionOut:
    def test_valid(self):
        schema = SubscriptionOut(
            user_id="user_1",
            plan_code="professional",
            status="active",
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            auto_renew=True,
        )
        assert schema.user_id == "user_1"

    def test_optional_fields_default_to_none(self):
        schema = SubscriptionOut(
            user_id="user_1",
            plan_code="basic",
            status="active",
            started_at=datetime.utcnow(),
        )
        assert schema.expires_at is None
        assert schema.canceled_at is None
        assert schema.recurring_token is None


# ======================================================================
# Plan schemas
# ======================================================================


class TestPlanOut:
    def test_valid(self):
        schema = PlanOut(
            code="basic",
            name="Basic",
            period_days=30,
            is_active=True,
            version=1,
        )
        assert schema.code == "basic"


class TestPlanWithFeaturesOut:
    def test_valid_with_features(self):
        features = {
            "accounts": PlanFeatureOut(
                code="accounts",
                name="Accounts",
                enabled=True,
                limit_value=5,
            )
        }
        schema = PlanWithFeaturesOut(
            code="basic",
            name="Basic",
            period_days=30,
            is_active=True,
            version=1,
            features=features,
        )
        assert "accounts" in schema.features
        assert schema.features["accounts"].limit_value == 5


# ======================================================================
# Entitlements schemas
# ======================================================================


class TestEntitlementsOut:
    def test_valid(self):
        schema = EntitlementsOut(
            user_id="user_1",
            plan_code="professional",
            version=2,
            entitlements={"accounts": {"enabled": True, "limit_value": 10}},
        )
        # Schema type is Dict[str, Dict[str, Optional[int]]], so bool -> int
        assert schema.entitlements["accounts"]["enabled"] == 1
        assert schema.entitlements["accounts"]["limit_value"] == 10

    def test_empty_entitlements(self):
        schema = EntitlementsOut(
            user_id="user_1",
            plan_code="free",
            version=1,
            entitlements={},
        )
        assert schema.entitlements == {}


# ======================================================================
# Feature schemas
# ======================================================================


class TestFeatureOut:
    def test_valid(self):
        schema = FeatureOut(code="accounts", name="Accounts")
        assert schema.description is None

    def test_with_description(self):
        schema = FeatureOut(
            code="accounts",
            name="Accounts",
            description="Manage financial accounts",
        )
        assert schema.description == "Manage financial accounts"


class TestUserFeatureOut:
    def test_valid(self):
        schema = UserFeatureOut(
            feature_code="accounts",
            enabled=True,
            limit_value=10,
            plan_code="professional",
        )
        assert schema.plan_code == "professional"


# ======================================================================
# Cancellation schemas
# ======================================================================


class TestCancelSubscriptionRequest:
    def test_defaults(self):
        schema = CancelSubscriptionRequest()
        assert schema.cancellation_reason is None
        assert schema.cancellation_comment is None
        assert schema.cancel_immediately is False

    def test_with_all_fields(self):
        schema = CancelSubscriptionRequest(
            cancellation_reason="too_expensive",
            cancellation_comment="I found a cheaper alternative",
            cancel_immediately=True,
        )
        assert schema.cancel_immediately is True
        assert schema.cancellation_reason == "too_expensive"

    def test_reason_max_length(self):
        """Reason must not exceed 32 characters."""
        with pytest.raises(PydanticValidationError):
            CancelSubscriptionRequest(
                cancellation_reason="x" * 33,
            )

    def test_comment_max_length(self):
        """Comment must not exceed 500 characters."""
        with pytest.raises(PydanticValidationError):
            CancelSubscriptionRequest(
                cancellation_comment="x" * 501,
            )


class TestCancelSubscriptionResponse:
    def test_valid(self):
        schema = CancelSubscriptionResponse(
            id=1,
            user_id="user_1",
            plan_code="professional",
            status="canceled",
            auto_renew=False,
            canceled_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            cancellation_reason="too_expensive",
            access_ends_at=datetime.utcnow(),
            message="Subscription canceled.",
        )
        assert schema.auto_renew is False


# ======================================================================
# Consent schemas
# ======================================================================


class TestConsentRecordRequest:
    def test_valid(self):
        schema = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Professional",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )
        assert schema.currency == "USD"

    def test_currency_uppercased(self):
        schema = ConsentRecordRequest(
            subscription_id=1,
            consent_version="v1.0.0",
            consent_language="en",
            plan_name="Pro",
            plan_code="professional",
            amount="29.99",
            currency="usd",
        )
        assert schema.currency == "USD"

    def test_invalid_language_raises(self):
        with pytest.raises(PydanticValidationError):
            ConsentRecordRequest(
                subscription_id=1,
                consent_version="v1.0.0",
                consent_language="de",
                plan_name="Pro",
                plan_code="professional",
                amount="29.99",
                currency="USD",
            )

    def test_currency_wrong_length_raises(self):
        with pytest.raises(PydanticValidationError):
            ConsentRecordRequest(
                subscription_id=1,
                consent_version="v1.0.0",
                consent_language="en",
                plan_name="Pro",
                plan_code="professional",
                amount="29.99",
                currency="USDX",
            )

    def test_empty_consent_version_raises(self):
        with pytest.raises(PydanticValidationError):
            ConsentRecordRequest(
                subscription_id=1,
                consent_version="",
                consent_language="en",
                plan_name="Pro",
                plan_code="professional",
                amount="29.99",
                currency="USD",
            )


class TestConsentVersionResponse:
    def test_valid(self):
        schema = ConsentVersionResponse(
            version="v1.0.0",
            supported_languages=["en", "uk"],
        )
        assert len(schema.supported_languages) == 2


# ======================================================================
# Admin schemas
# ======================================================================


class TestPlanCreate:
    def test_valid(self):
        schema = PlanCreate(code="pro_monthly", name="Pro Monthly", period_days=30)
        assert schema.is_active is True

    def test_code_pattern_must_start_with_lowercase(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="Pro", name="Pro", period_days=30)

    def test_code_pattern_no_special_chars(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="pro-monthly", name="Pro", period_days=30)

    def test_code_allows_underscores(self):
        schema = PlanCreate(code="pro_monthly_v2", name="Pro", period_days=30)
        assert schema.code == "pro_monthly_v2"

    def test_empty_name_raises(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="", period_days=30)

    def test_period_days_must_be_positive(self):
        with pytest.raises(PydanticValidationError):
            PlanCreate(code="basic", name="Basic", period_days=0)


class TestPlanUpdate:
    def test_all_optional(self):
        schema = PlanUpdate()
        assert schema.name is None
        assert schema.period_days is None
        assert schema.is_active is None

    def test_partial_update(self):
        schema = PlanUpdate(name="Updated Name")
        assert schema.name == "Updated Name"
        assert schema.period_days is None


class TestPlanFeaturesUpdate:
    def test_valid(self):
        schema = PlanFeaturesUpdate(
            features=[
                PlanFeatureIn(feature_code="accounts", enabled=True, limit_value=10),
                PlanFeatureIn(feature_code="categories", enabled=False),
            ]
        )
        assert len(schema.features) == 2


class TestSubscriptionStatsOut:
    def test_valid(self):
        schema = SubscriptionStatsOut(
            total=100,
            active=80,
            past_due=10,
            canceled=8,
            paused=2,
        )
        assert schema.total == 100


class TestAdminSubscriptionsListResponse:
    def test_valid(self):
        schema = AdminSubscriptionsListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert schema.total == 0
