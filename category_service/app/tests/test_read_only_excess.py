"""
Tests for read-only excess behavior in CategoryService.

Covers:
1. Service-level: _check_modify_allowed, create limit checks
2. Router-level: is_read_only flag in list responses
3. Full downgrade flow: pro -> free with excess categories
"""
import time
import pytest
from unittest.mock import patch
from uuid import UUID
from random import randint
from datetime import datetime, timedelta

from app.services.category import CategoryService
from app.models.category import Category, CategoryType as ModelCategoryType
from app.schemas.category import CategoryCreate
from app.exceptions import (
    CategoryLimitExceededError,
    CategoryReadOnlyExcessError,
)
from app.tests.conftest import TEST_WORKSPACE_ID, TEST_WORKSPACE_ID_HEADER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_category_with_time(
    db, user_id, workspace_id, name, created_at=None
):
    """Create a Category directly in DB with an explicit created_at."""
    cat = Category(
        name=name,
        user_id=user_id,
        workspace_id=workspace_id,
        type=ModelCategoryType.EXPENSE,
    )
    db.add(cat)
    db.flush()
    if created_at is not None:
        db.execute(
            Category.__table__.update()
            .where(Category.__table__.c.id == cat.id)
            .values(created_at=created_at)
        )
        db.commit()
        db.refresh(cat)
    else:
        db.commit()
        db.refresh(cat)
    return cat


def _subscription_features(limit_value):
    """Return a features dict used by SubscriptionClient mocks."""
    return {
        "categories": {
            "enabled": True,
            "limit_value": limit_value,
        }
    }


# ---------------------------------------------------------------------------
# 1. Service-level tests: _check_modify_allowed
# ---------------------------------------------------------------------------

class TestCheckModifyAllowed:
    """Tests for CategoryService._check_modify_allowed."""

    def test_edit_oldest_within_limit_allowed(self, db):
        """Editing the oldest category when within limit should succeed."""
        user_id = randint(400000, 405000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440010")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cat1 = _create_category_with_time(db, user_id, ws, f"First{user_id}", base_time)
        cat2 = _create_category_with_time(
            db, user_id, ws, f"Second{user_id}", base_time + timedelta(seconds=1)
        )

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(5),
        ):
            # Should not raise -- 2 categories, limit is 5
            service._check_modify_allowed(cat1.id, user_id, ws)

    def test_edit_newest_excess_raises(self, db):
        """Editing the newest (excess) category when over limit should raise."""
        user_id = randint(405000, 410000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440011")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(3):
            cat = _create_category_with_time(
                db, user_id, ws, f"Cat{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        # Limit = 2, so cats[2] (newest) is excess
        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(2),
        ):
            with pytest.raises(CategoryReadOnlyExcessError):
                service._check_modify_allowed(cats[2].id, user_id, ws)

    def test_edit_oldest_when_over_limit_allowed(self, db):
        """Editing the oldest category when over limit should still succeed."""
        user_id = randint(410000, 415000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440012")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(3):
            cat = _create_category_with_time(
                db, user_id, ws, f"Cat{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        # Limit = 2 => cats[0] and cats[1] are editable
        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(2),
        ):
            service._check_modify_allowed(cats[0].id, user_id, ws)

    def test_update_excess_category_raises(self, db):
        """Full update() call on an excess category should raise CategoryReadOnlyExcessError."""
        user_id = randint(415000, 420000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440013")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(3):
            cat = _create_category_with_time(
                db, user_id, ws, f"UpdExc{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        data = CategoryCreate(name=f"Renamed{user_id}")

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(2),
        ), patch(
            "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
            wraps=service.subscription_client.check_modify_allowed,
        ):
            with pytest.raises(CategoryReadOnlyExcessError):
                service.update(cats[2].id, data, user_id, ws)

    def test_update_oldest_within_limit_succeeds(self, db):
        """Full update() call on an editable category should succeed."""
        user_id = randint(420000, 425000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440014")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(3):
            cat = _create_category_with_time(
                db, user_id, ws, f"UpdOk{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        new_name = f"RenamedOk{user_id}"
        data = CategoryCreate(name=new_name)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(2),
        ), patch(
            "shared.clients.subscription.SubscriptionClient.check_limit",
            return_value=(True, None),
        ):
            result = service.update(cats[0].id, data, user_id, ws)
            assert result.name == new_name


# ---------------------------------------------------------------------------
# 2. Service-level tests: delete does NOT check _check_modify_allowed
# ---------------------------------------------------------------------------

class TestDeleteBypassesModifyCheck:
    """Delete should succeed even for read-only (excess) categories."""

    def test_delete_excess_category_succeeds(self, db):
        """A category that is read-only for edits can still be deleted."""
        user_id = randint(425000, 430000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440015")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(3):
            cat = _create_category_with_time(
                db, user_id, ws, f"Del{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        # Limit = 2 => cats[2] is excess / read-only for edits
        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(2),
        ):
            result = service.delete(cats[2].id, user_id, ws)
            assert "deleted" in result["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Service-level tests: create limit checks
# ---------------------------------------------------------------------------

class TestCreateLimitChecks:

    def test_create_at_limit_raises(self, db):
        """Creating a category when already at the limit should raise."""
        user_id = randint(430000, 435000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440016")
        service = CategoryService(db)

        # Create 3 categories
        for i in range(3):
            _create_category_with_time(
                db, user_id, ws, f"Lim{user_id}_{i}"
            )

        data = CategoryCreate(name=f"OneMore{user_id}")

        with patch(
            "shared.clients.subscription.SubscriptionClient.check_limit",
            return_value=(False, 3),
        ), patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(3),
        ):
            with pytest.raises(CategoryLimitExceededError):
                service.create(data, user_id, ws)

    def test_create_under_limit_succeeds(self, db):
        """Creating a category under the limit should succeed."""
        user_id = randint(435000, 440000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440017")
        service = CategoryService(db)

        data = CategoryCreate(name=f"Under{user_id}")

        with patch(
            "shared.clients.subscription.SubscriptionClient.check_limit",
            return_value=(True, None),
        ), patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(20),
        ):
            result = service.create(data, user_id, ws)
            assert result.name == f"Under{user_id}"


# ---------------------------------------------------------------------------
# 4. Router-level tests: is_read_only in list responses
# ---------------------------------------------------------------------------

class TestRouterIsReadOnly:

    def test_list_within_limit_all_editable(self, client, db):
        """When total categories <= limit, all should have is_read_only=false."""
        user_id = randint(440000, 445000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440018")
        ws_header = str(ws)

        base_time = datetime(2025, 1, 1)
        for i in range(3):
            _create_category_with_time(
                db, user_id, ws, f"RoAll{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )

        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch("app.dependencies.get_workspace_id", return_value=ws), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_user_features",
                 return_value=_subscription_features(10),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.check_limit",
                 return_value=(True, None),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                 return_value=set(),
             ):
            from app.main import app
            from app.dependencies import get_workspace_id
            original = app.dependency_overrides.get(get_workspace_id)
            app.dependency_overrides[get_workspace_id] = lambda: ws
            try:
                response = client.get(
                    "/categories/?flat=true",
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": ws_header,
                    },
                )
            finally:
                if original is not None:
                    app.dependency_overrides[get_workspace_id] = original

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_read_only"] is False

    def test_list_over_limit_marks_excess_read_only(self, client, db):
        """When over limit, oldest N are editable, rest are read-only."""
        user_id = randint(445000, 450000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440019")
        ws_header = str(ws)
        limit = 2

        base_time = datetime(2025, 6, 1)
        cats = []
        for i in range(4):
            cat = _create_category_with_time(
                db, user_id, ws, f"RoOver{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        # Oldest 2 (cats[0], cats[1]) editable; cats[2], cats[3] read-only
        excess_ids = {cats[2].id, cats[3].id}
        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_user_features",
                 return_value=_subscription_features(limit),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.check_limit",
                 return_value=(True, None),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                 return_value=excess_ids,
             ):
            from app.main import app
            from app.dependencies import get_workspace_id
            original = app.dependency_overrides.get(get_workspace_id)
            app.dependency_overrides[get_workspace_id] = lambda: ws
            try:
                response = client.get(
                    "/categories/?flat=true&size=100",
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": ws_header,
                    },
                )
            finally:
                if original is not None:
                    app.dependency_overrides[get_workspace_id] = original

        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        editable_ids = {cats[0].id, cats[1].id}
        read_only_ids = {cats[2].id, cats[3].id}

        for item in items:
            if item["id"] in editable_ids:
                assert item["is_read_only"] is False, (
                    f"Category {item['id']} should be editable (oldest N)"
                )
            elif item["id"] in read_only_ids:
                assert item["is_read_only"] is True, (
                    f"Category {item['id']} should be read-only (excess)"
                )

    def test_ordering_by_created_at_determines_read_only(self, client, db):
        """Verify that created_at ASC ordering determines which categories are read-only."""
        user_id = randint(450000, 455000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440020")
        ws_header = str(ws)
        limit = 2

        # Create cats with explicit ordering: cat_b is older than cat_a
        cat_b = _create_category_with_time(
            db, user_id, ws, f"OrderB{user_id}",
            datetime(2025, 1, 1),
        )
        cat_a = _create_category_with_time(
            db, user_id, ws, f"OrderA{user_id}",
            datetime(2025, 6, 1),
        )
        cat_c = _create_category_with_time(
            db, user_id, ws, f"OrderC{user_id}",
            datetime(2025, 12, 1),
        )

        # limit=2 => cat_b (oldest) and cat_a (second oldest) editable, cat_c read-only
        excess_ids = {cat_c.id}
        with patch("shared.auth.dependencies.decode_token", return_value=user_id), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_user_features",
                 return_value=_subscription_features(limit),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.check_limit",
                 return_value=(True, None),
             ), \
             patch(
                 "shared.clients.subscription.SubscriptionClient.get_read_only_ids",
                 return_value=excess_ids,
             ):
            from app.main import app
            from app.dependencies import get_workspace_id
            original = app.dependency_overrides.get(get_workspace_id)
            app.dependency_overrides[get_workspace_id] = lambda: ws
            try:
                response = client.get(
                    "/categories/?flat=true&size=100",
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": ws_header,
                    },
                )
            finally:
                if original is not None:
                    app.dependency_overrides[get_workspace_id] = original

        assert response.status_code == 200
        items_by_id = {item["id"]: item for item in response.json()["items"]}

        assert items_by_id[cat_b.id]["is_read_only"] is False
        assert items_by_id[cat_a.id]["is_read_only"] is False
        assert items_by_id[cat_c.id]["is_read_only"] is True


# ---------------------------------------------------------------------------
# 5. Full downgrade flow
# ---------------------------------------------------------------------------

class TestDowngradeFlow:
    """Simulate plan changes (pro -> free) and verify read-only behavior."""

    def test_all_editable_when_within_free_limit(self, db):
        """Create 5 categories with pro limit (20), then check with free limit (5).
        All 5 should be editable because 5 == limit."""
        user_id = randint(455000, 460000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440021")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(5):
            cat = _create_category_with_time(
                db, user_id, ws, f"Pro{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        # "Downgrade" to free with limit=5. All 5 fit within limit.
        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(5),
        ):
            for cat in cats:
                service._check_modify_allowed(cat.id, user_id, ws)

    def test_excess_after_downgrade(self, db):
        """Create 6 categories on pro, downgrade to free (limit=5).
        Oldest 5 editable, 6th read-only."""
        user_id = randint(460000, 465000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440022")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(6):
            cat = _create_category_with_time(
                db, user_id, ws, f"Dwn{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(5),
        ):
            # Oldest 5 should be editable
            for cat in cats[:5]:
                service._check_modify_allowed(cat.id, user_id, ws)

            # 6th (newest) is read-only for edits
            with pytest.raises(CategoryReadOnlyExcessError):
                service._check_modify_allowed(cats[5].id, user_id, ws)

    def test_excess_can_still_be_deleted(self, db):
        """The 6th (read-only) category can still be deleted."""
        user_id = randint(465000, 470000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440023")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(6):
            cat = _create_category_with_time(
                db, user_id, ws, f"DelDwn{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(5),
        ):
            # Confirm it IS read-only for edits
            with pytest.raises(CategoryReadOnlyExcessError):
                service._check_modify_allowed(cats[5].id, user_id, ws)

            # But delete still works
            result = service.delete(cats[5].id, user_id, ws)
            assert "deleted" in result["detail"].lower()

    def test_downgrade_flow_with_update(self, db):
        """End-to-end: update oldest (allowed) and newest (blocked) after downgrade."""
        user_id = randint(470000, 475000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440024")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(6):
            cat = _create_category_with_time(
                db, user_id, ws, f"UpdDwn{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        features_free = _subscription_features(5)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=features_free,
        ), patch(
            "shared.clients.subscription.SubscriptionClient.check_limit",
            return_value=(True, None),
        ):
            # Update oldest -> should succeed
            new_name_ok = f"RenamedOldest{user_id}"
            result = service.update(
                cats[0].id,
                CategoryCreate(name=new_name_ok),
                user_id,
                ws,
            )
            assert result.name == new_name_ok

            # Update newest -> should fail
            with pytest.raises(CategoryReadOnlyExcessError):
                service.update(
                    cats[5].id,
                    CategoryCreate(name=f"RenamedNewest{user_id}"),
                    user_id,
                    ws,
                )


# ---------------------------------------------------------------------------
# 6. Edge cases
# ---------------------------------------------------------------------------

class TestReadOnlyEdgeCases:

    def test_features_none_fails_open(self, db):
        """When subscription service returns None, all records are editable."""
        user_id = randint(475000, 480000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440025")
        service = CategoryService(db)

        cat = _create_category_with_time(db, user_id, ws, f"FailOpen{user_id}")

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=None,
        ):
            # Should not raise (fail-open)
            service._check_modify_allowed(cat.id, user_id, ws)

    def test_feature_not_enabled_fails_open(self, db):
        """When feature is not enabled, all records are editable."""
        user_id = randint(480000, 485000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440026")
        service = CategoryService(db)

        cat = _create_category_with_time(db, user_id, ws, f"NotEnabled{user_id}")

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value={"categories": {"enabled": False, "limit_value": 1}},
        ):
            service._check_modify_allowed(cat.id, user_id, ws)

    def test_limit_none_means_unlimited(self, db):
        """When limit_value is None, all records are editable."""
        user_id = randint(485000, 490000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440027")
        service = CategoryService(db)

        cats = []
        for i in range(5):
            cat = _create_category_with_time(
                db, user_id, ws, f"Unlim{user_id}_{i}"
            )
            cats.append(cat)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value={"categories": {"enabled": True, "limit_value": None}},
        ):
            for cat in cats:
                service._check_modify_allowed(cat.id, user_id, ws)

    def test_exactly_at_limit_all_editable(self, db):
        """When count == limit, none are excess."""
        user_id = randint(490000, 495000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440028")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(5):
            cat = _create_category_with_time(
                db, user_id, ws, f"Exact{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(5),
        ):
            for cat in cats:
                service._check_modify_allowed(cat.id, user_id, ws)

    def test_one_over_limit_marks_only_newest(self, db):
        """When count == limit + 1, only the newest is read-only."""
        user_id = randint(495000, 500000)
        ws = UUID("cc0e8400-e29b-41d4-a716-446655440029")
        service = CategoryService(db)

        base_time = datetime(2025, 1, 1)
        cats = []
        for i in range(4):
            cat = _create_category_with_time(
                db, user_id, ws, f"OneOver{user_id}_{i}",
                base_time + timedelta(seconds=i),
            )
            cats.append(cat)

        with patch(
            "shared.clients.subscription.SubscriptionClient.get_user_features",
            return_value=_subscription_features(3),
        ):
            # First 3 editable
            for cat in cats[:3]:
                service._check_modify_allowed(cat.id, user_id, ws)

            # Only the 4th is read-only
            with pytest.raises(CategoryReadOnlyExcessError):
                service._check_modify_allowed(cats[3].id, user_id, ws)
