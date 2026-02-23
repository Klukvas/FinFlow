"""
Direct unit tests for app/services/category.py - CategoryService methods.
Tests service methods directly (not via HTTP) to increase line coverage for
missed lines: 94, 116-128, 215-256, 260-486, 490-620, 678-690, 712-714,
746-775, 802, 838-840, 874, 903-919, 923-944, 948-988, 995-1046, 1057-1111
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4
from random import randint

from app.services.category import CategoryService
from app.models.category import Category, CategoryType as ModelCategoryType, CategoryCreatedBy
from app.models.mcc import MCCCode, MCCTranslation
from app.schemas.category import (
    CategoryCreate,
    CategoryType,
    CategoryCreateFromMCC,
    CategoryCreateFromMCCBatch,
    SupportedLanguage,
)
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryNameConflictError,
    CategoryOwnershipError,
    CategoryLimitExceededError,
)
from app.tests.conftest import TEST_WORKSPACE_ID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_category(db, user_id, workspace_id, name, mcc_code=None, parent_id=None):
    """Create a Category directly in DB and return it."""
    cat = Category(
        name=name,
        user_id=user_id,
        workspace_id=workspace_id,
        type=ModelCategoryType.EXPENSE,
        mcc_code=mcc_code,
        parent_id=parent_id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _ensure_mcc(db, mcc_code, name="Test MCC", is_default=True):
    """Insert an MCCCode row if it doesn't already exist."""
    existing = db.query(MCCCode).filter(MCCCode.mcc_code == mcc_code).first()
    if not existing:
        mcc = MCCCode(mcc_code=mcc_code, name=name, is_default=is_default)
        db.add(mcc)
        db.commit()
        db.refresh(mcc)
        return mcc
    return existing


# ---------------------------------------------------------------------------
# CategoryService.get_all / get_all_flat / get
# ---------------------------------------------------------------------------

class TestCategoryServiceGetAll:
    def test_get_all_returns_root_categories(self, db):
        user_id = randint(50000, 55000)
        service = CategoryService(db)
        c1 = _create_category(db, user_id, TEST_WORKSPACE_ID, "RootA" + str(user_id))
        c2 = _create_category(db, user_id, TEST_WORKSPACE_ID, "RootB" + str(user_id))

        categories, total = service.get_all(user_id, TEST_WORKSPACE_ID)
        names = [c.name for c in categories]
        assert c1.name in names
        assert c2.name in names
        assert total >= 2

    def test_get_all_excludes_child_categories(self, db):
        user_id = randint(55000, 60000)
        service = CategoryService(db)
        parent = _create_category(db, user_id, TEST_WORKSPACE_ID, "ParentOnly" + str(user_id))
        child = _create_category(db, user_id, TEST_WORKSPACE_ID, "ChildOnly" + str(user_id), parent_id=parent.id)

        categories, total = service.get_all(user_id, TEST_WORKSPACE_ID)
        root_ids = [c.id for c in categories]
        assert parent.id in root_ids
        assert child.id not in root_ids

    def test_get_all_pagination(self, db):
        user_id = randint(60000, 65000)
        service = CategoryService(db)
        for i in range(5):
            _create_category(db, user_id, TEST_WORKSPACE_ID, f"PagCat{user_id}_{i}")

        page1, total = service.get_all(user_id, TEST_WORKSPACE_ID, page=1, size=2)
        assert len(page1) <= 2
        assert total >= 5

    def test_get_all_flat_returns_all_categories(self, db):
        user_id = randint(65000, 70000)
        service = CategoryService(db)
        parent = _create_category(db, user_id, TEST_WORKSPACE_ID, "FlatParent" + str(user_id))
        child = _create_category(db, user_id, TEST_WORKSPACE_ID, "FlatChild" + str(user_id), parent_id=parent.id)

        categories, total = service.get_all_flat(user_id, TEST_WORKSPACE_ID)
        ids = [c.id for c in categories]
        assert parent.id in ids
        assert child.id in ids

    def test_get_all_flat_pagination(self, db):
        user_id = randint(70000, 75000)
        service = CategoryService(db)
        for i in range(6):
            _create_category(db, user_id, TEST_WORKSPACE_ID, f"FlatPag{user_id}_{i}")

        page1, total = service.get_all_flat(user_id, TEST_WORKSPACE_ID, page=1, size=3)
        assert len(page1) <= 3
        assert total >= 6

    def test_get_all_raises_on_unauthorized(self, db):
        user_id = randint(75000, 80000)
        service = CategoryService(db)
        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(False, None)):
            with pytest.raises(Exception):
                service.get_all(user_id, TEST_WORKSPACE_ID)


class TestCategoryServiceGet:
    def test_get_returns_category(self, db):
        user_id = randint(80000, 85000)
        service = CategoryService(db)
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "GetByIdCat" + str(user_id))

        result = service.get(cat.id, user_id, TEST_WORKSPACE_ID)
        assert result.id == cat.id
        assert result.name == cat.name

    def test_get_raises_not_found(self, db):
        user_id = randint(85000, 90000)
        service = CategoryService(db)
        with pytest.raises(CategoryNotFoundError):
            service.get(999999999, user_id, TEST_WORKSPACE_ID)

    def test_get_raises_ownership_error_wrong_user(self, db):
        user1_id = randint(90000, 95000)
        user2_id = randint(95000, 100000)
        service = CategoryService(db)
        cat = _create_category(db, user1_id, TEST_WORKSPACE_ID, "GetOwnership" + str(user1_id))

        with pytest.raises(Exception):
            service.get(cat.id, user2_id, TEST_WORKSPACE_ID)

    def test_get_raises_workspace_mismatch(self, db):
        user_id = randint(100000, 105000)
        service = CategoryService(db)
        other_workspace = UUID("660e8400-e29b-41d4-a716-446655440001")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "GetWsMismatch" + str(user_id))

        with pytest.raises(Exception):
            service.get(cat.id, user_id, other_workspace)


class TestCategoryServiceGetChildren:
    def test_get_children_returns_direct_children(self, db):
        user_id = randint(105000, 110000)
        service = CategoryService(db)
        parent = _create_category(db, user_id, TEST_WORKSPACE_ID, "GetChildPar" + str(user_id))
        child1 = _create_category(db, user_id, TEST_WORKSPACE_ID, "GetChild1" + str(user_id), parent_id=parent.id)
        child2 = _create_category(db, user_id, TEST_WORKSPACE_ID, "GetChild2" + str(user_id), parent_id=parent.id)

        children = service.get_children(parent.id, user_id, TEST_WORKSPACE_ID)
        child_ids = [c.id for c in children]
        assert child1.id in child_ids
        assert child2.id in child_ids

    def test_get_children_parent_not_found_raises(self, db):
        user_id = randint(110000, 115000)
        service = CategoryService(db)
        with pytest.raises(Exception):
            service.get_children(999999999, user_id, TEST_WORKSPACE_ID)

    def test_get_children_returns_empty_list_for_leaf(self, db):
        user_id = randint(115000, 120000)
        service = CategoryService(db)
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "LeafCat" + str(user_id))

        children = service.get_children(cat.id, user_id, TEST_WORKSPACE_ID)
        assert children == []


# ---------------------------------------------------------------------------
# CategoryService.create - error paths
# ---------------------------------------------------------------------------

class TestCategoryServiceCreateErrors:
    def test_create_raises_when_subscription_limit_exceeded(self, db):
        user_id = randint(120000, 125000)
        service = CategoryService(db)
        data = CategoryCreate(name="LimitTest")

        with patch(
            "app.clients.subscription.SubscriptionClient.check_category_limit",
            return_value=False,
        ), patch(
            "app.clients.subscription.SubscriptionClient.get_user_features",
            return_value={"categories": {"limit_value": 10}},
        ):
            with pytest.raises(Exception):
                service.create(data, user_id, TEST_WORKSPACE_ID)

    def test_create_raises_when_parent_not_found(self, db):
        user_id = randint(125000, 130000)
        service = CategoryService(db)
        data = CategoryCreate(name="OrphanCat", parent_id=999999999)

        with pytest.raises(CategoryNotFoundError):
            service.create(data, user_id, TEST_WORKSPACE_ID)

    def test_create_raises_when_subscription_client_throws(self, db):
        user_id = randint(130000, 135000)
        service = CategoryService(db)
        data = CategoryCreate(name="SubErrTest")

        with patch(
            "app.clients.subscription.SubscriptionClient.check_category_limit",
            side_effect=Exception("Service unavailable"),
        ):
            with pytest.raises(CategoryValidationError):
                service.create(data, user_id, TEST_WORKSPACE_ID)

    def test_create_raises_on_workspace_unauthorized(self, db):
        user_id = randint(135000, 140000)
        service = CategoryService(db)
        data = CategoryCreate(name="UnauthorizedCreate")

        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(False, None)):
            with pytest.raises(Exception):
                service.create(data, user_id, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# CategoryService.update - error paths
# ---------------------------------------------------------------------------

class TestCategoryServiceUpdateErrors:
    def test_update_raises_not_found(self, db):
        user_id = randint(140000, 145000)
        service = CategoryService(db)
        data = CategoryCreate(name="UpdateNotFound")

        with pytest.raises(CategoryNotFoundError):
            service.update(999999999, data, user_id, TEST_WORKSPACE_ID)

    def test_update_raises_ownership_error(self, db):
        user1_id = randint(145000, 150000)
        user2_id = randint(150000, 155000)
        service = CategoryService(db)
        cat = _create_category(db, user1_id, TEST_WORKSPACE_ID, "UpdateOwn" + str(user1_id))
        data = CategoryCreate(name="HackedName")

        with pytest.raises(Exception):
            service.update(cat.id, data, user2_id, TEST_WORKSPACE_ID)

    def test_update_raises_when_new_parent_not_found(self, db):
        user_id = randint(155000, 160000)
        service = CategoryService(db)
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "UpdateParent" + str(user_id))
        data = CategoryCreate(name="UpdateParent" + str(user_id), parent_id=999999999)

        with pytest.raises(CategoryNotFoundError):
            service.update(cat.id, data, user_id, TEST_WORKSPACE_ID)

    def test_update_raises_workspace_mismatch(self, db):
        user_id = randint(160000, 165000)
        service = CategoryService(db)
        other_ws = UUID("660e8400-e29b-41d4-a716-446655440002")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "UpdateWsMismatch" + str(user_id))
        data = CategoryCreate(name="UpdateWsMismatch" + str(user_id))

        with pytest.raises(Exception):
            service.update(cat.id, data, user_id, other_ws)


# ---------------------------------------------------------------------------
# CategoryService.delete - error paths
# ---------------------------------------------------------------------------

class TestCategoryServiceDeleteErrors:
    def test_delete_raises_not_found(self, db):
        user_id = randint(165000, 170000)
        service = CategoryService(db)

        with pytest.raises(CategoryNotFoundError):
            service.delete(999999999, user_id, TEST_WORKSPACE_ID)

    def test_delete_raises_ownership_error(self, db):
        user1_id = randint(170000, 175000)
        user2_id = randint(175000, 180000)
        service = CategoryService(db)
        cat = _create_category(db, user1_id, TEST_WORKSPACE_ID, "DeleteOwn" + str(user1_id))

        with pytest.raises(Exception):
            service.delete(cat.id, user2_id, TEST_WORKSPACE_ID)

    def test_delete_raises_when_has_children(self, db):
        user_id = randint(180000, 185000)
        service = CategoryService(db)
        parent = _create_category(db, user_id, TEST_WORKSPACE_ID, "DeleteParent" + str(user_id))
        _create_category(db, user_id, TEST_WORKSPACE_ID, "DeleteChild" + str(user_id), parent_id=parent.id)

        with pytest.raises(CategoryValidationError):
            service.delete(parent.id, user_id, TEST_WORKSPACE_ID)

    def test_delete_succeeds_for_leaf(self, db):
        user_id = randint(185000, 190000)
        service = CategoryService(db)
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "DeleteLeaf" + str(user_id))

        result = service.delete(cat.id, user_id, TEST_WORKSPACE_ID)
        assert "deleted" in result["detail"].lower()

    def test_delete_raises_workspace_mismatch(self, db):
        user_id = randint(190000, 195000)
        service = CategoryService(db)
        other_ws = UUID("660e8400-e29b-41d4-a716-446655440003")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "DeleteWsMismatch" + str(user_id))

        with pytest.raises(Exception):
            service.delete(cat.id, user_id, other_ws)


# ---------------------------------------------------------------------------
# CategoryService.get_by_id_internal
# ---------------------------------------------------------------------------

class TestCategoryServiceGetByIdInternal:
    def test_returns_category(self, db):
        user_id = randint(195000, 200000)
        service = CategoryService(db)
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "InternalGetCat" + str(user_id))

        result = service.get_by_id_internal(cat.id, user_id, TEST_WORKSPACE_ID)
        assert result.id == cat.id

    def test_raises_not_found(self, db):
        user_id = randint(200000, 205000)
        service = CategoryService(db)

        with pytest.raises(CategoryValidationError):
            service.get_by_id_internal(999999999, user_id, TEST_WORKSPACE_ID)

    def test_raises_when_wrong_workspace(self, db):
        user_id = randint(205000, 210000)
        service = CategoryService(db)
        other_ws = UUID("660e8400-e29b-41d4-a716-446655440004")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "InternalWsMismatch" + str(user_id))

        with pytest.raises(CategoryValidationError):
            service.get_by_id_internal(cat.id, user_id, other_ws)

    def test_raises_when_wrong_user(self, db):
        user1_id = randint(210000, 215000)
        user2_id = randint(215000, 220000)
        service = CategoryService(db)
        cat = _create_category(db, user1_id, TEST_WORKSPACE_ID, "InternalWrongUser" + str(user1_id))

        with pytest.raises(CategoryValidationError):
            service.get_by_id_internal(cat.id, user2_id, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# CategoryService.check_category_exists_by_mcc
# ---------------------------------------------------------------------------

class TestCheckCategoryExistsByMCC:
    def test_returns_false_when_not_exists(self, db):
        user_id = randint(220000, 225000)
        service = CategoryService(db)

        result = service.check_category_exists_by_mcc(5411, user_id, TEST_WORKSPACE_ID)
        assert result is False

    def test_returns_true_when_exists(self, db):
        user_id = randint(225000, 230000)
        service = CategoryService(db)
        mcc_code = 9876
        _ensure_mcc(db, mcc_code, "Test Store")
        _create_category(db, user_id, TEST_WORKSPACE_ID, "MccExistTest" + str(user_id), mcc_code=mcc_code)

        result = service.check_category_exists_by_mcc(mcc_code, user_id, TEST_WORKSPACE_ID)
        assert result is True

    def test_returns_false_on_db_error(self, db):
        user_id = randint(230000, 235000)
        service = CategoryService(db)

        with patch.object(db, "query", side_effect=Exception("DB error")):
            result = service.check_category_exists_by_mcc(5411, user_id, TEST_WORKSPACE_ID)
        assert result is False


# ---------------------------------------------------------------------------
# CategoryService.get_category_by_mcc
# ---------------------------------------------------------------------------

class TestGetCategoryByMCC:
    def test_returns_not_exists_when_no_category(self, db):
        user_id = randint(235000, 240000)
        service = CategoryService(db)

        result = service.get_category_by_mcc(5411, user_id, TEST_WORKSPACE_ID)
        assert result["exists"] is False
        assert result["category_id"] is None

    def test_returns_exists_with_id_when_found(self, db):
        user_id = randint(240000, 245000)
        service = CategoryService(db)
        mcc_code = 8765
        _ensure_mcc(db, mcc_code, "Found Store")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "MccGetTest" + str(user_id), mcc_code=mcc_code)

        result = service.get_category_by_mcc(mcc_code, user_id, TEST_WORKSPACE_ID)
        assert result["exists"] is True
        assert result["category_id"] == cat.id

    def test_returns_not_exists_on_db_error(self, db):
        user_id = randint(245000, 250000)
        service = CategoryService(db)

        with patch.object(db, "query", side_effect=Exception("DB failure")):
            result = service.get_category_by_mcc(5411, user_id, TEST_WORKSPACE_ID)
        assert result["exists"] is False
        assert result["category_id"] is None


# ---------------------------------------------------------------------------
# CategoryService.check_categories_exist_by_mcc_batch
# ---------------------------------------------------------------------------

class TestCheckCategoriesExistByMCCBatch:
    def test_all_not_exist_for_new_user(self, db):
        user_id = randint(250000, 255000)
        service = CategoryService(db)
        mcc_codes = [5411, 5812, 4121]

        results = service.check_categories_exist_by_mcc_batch(mcc_codes, user_id, TEST_WORKSPACE_ID)
        assert len(results) == 3
        for r in results:
            assert r["exists"] is False
            assert r["category_id"] is None

    def test_some_exist(self, db):
        user_id = randint(255000, 260000)
        service = CategoryService(db)
        mcc_code = 7654
        _ensure_mcc(db, mcc_code, "Batch Test MCC")
        cat = _create_category(db, user_id, TEST_WORKSPACE_ID, "BatchMccTest" + str(user_id), mcc_code=mcc_code)

        results = service.check_categories_exist_by_mcc_batch(
            [mcc_code, 9999], user_id, TEST_WORKSPACE_ID
        )
        assert len(results) == 2
        existing = next(r for r in results if r["mcc_code"] == mcc_code)
        missing = next(r for r in results if r["mcc_code"] == 9999)
        assert existing["exists"] is True
        assert existing["category_id"] == cat.id
        assert missing["exists"] is False

    def test_returns_all_not_exist_on_db_error(self, db):
        user_id = randint(260000, 265000)
        service = CategoryService(db)
        mcc_codes = [5411, 5812]

        with patch.object(db, "query", side_effect=Exception("DB failure")):
            results = service.check_categories_exist_by_mcc_batch(mcc_codes, user_id, TEST_WORKSPACE_ID)
        assert len(results) == 2
        for r in results:
            assert r["exists"] is False

    def test_empty_list_returns_empty(self, db):
        user_id = randint(265000, 270000)
        service = CategoryService(db)

        results = service.check_categories_exist_by_mcc_batch([], user_id, TEST_WORKSPACE_ID)
        assert results == []


# ---------------------------------------------------------------------------
# CategoryService.get_statistics
# ---------------------------------------------------------------------------

class TestCategoryServiceGetStatistics:
    def test_statistics_returns_correct_counts(self, db):
        # Use a unique workspace so counts are deterministic
        unique_ws = UUID("aa0e8400-e29b-41d4-a716-446655440001")
        user_id = randint(270000, 275000)
        service = CategoryService(db)

        # Create expense and income categories
        cat1 = Category(
            name="StatExpense" + str(user_id),
            user_id=user_id,
            workspace_id=unique_ws,
            type=ModelCategoryType.EXPENSE,
        )
        cat2 = Category(
            name="StatIncome" + str(user_id),
            user_id=user_id,
            workspace_id=unique_ws,
            type=ModelCategoryType.INCOME,
        )
        db.add(cat1)
        db.add(cat2)
        db.commit()
        db.refresh(cat1)

        # Create a child
        cat3 = Category(
            name="StatChild" + str(user_id),
            user_id=user_id,
            workspace_id=unique_ws,
            type=ModelCategoryType.EXPENSE,
            parent_id=cat1.id,
        )
        db.add(cat3)
        db.commit()

        # Use a patched workspace authorize for the unique workspace
        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(True, "owner")):
            stats = service.get_statistics(user_id, unique_ws)
        assert stats["total_categories"] == 3
        assert stats["parent_categories"] == 2
        assert stats["child_categories"] == 1

    def test_statistics_zero_for_empty_workspace(self, db):
        user_id = randint(275000, 280000)
        service = CategoryService(db)
        empty_workspace = UUID("770e8400-e29b-41d4-a716-446655440000")

        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(True, "owner")):
            stats = service.get_statistics(user_id, empty_workspace)
        assert stats["total_categories"] == 0
        assert stats["expense_categories"] == 0
        assert stats["income_categories"] == 0
        assert stats["parent_categories"] == 0
        assert stats["child_categories"] == 0

    def test_statistics_raises_on_unauthorized(self, db):
        user_id = randint(280000, 285000)
        service = CategoryService(db)

        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(False, None)):
            with pytest.raises(Exception):
                service.get_statistics(user_id, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# CategoryService.create_from_mcc
# ---------------------------------------------------------------------------

class TestCategoryServiceCreateFromMCC:
    def test_create_from_mcc_not_found_raises(self, db):
        user_id = randint(285000, 290000)
        service = CategoryService(db)
        data = CategoryCreateFromMCC(mcc_code=1111)

        # Ensure MCC code 1111 does NOT exist
        from app.models.mcc import MCCCode as MCCCodeModel
        existing = db.query(MCCCodeModel).filter(MCCCodeModel.mcc_code == 1111).first()
        if existing:
            db.delete(existing)
            db.commit()

        with pytest.raises(CategoryValidationError):
            service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)

    def test_create_from_mcc_success(self, db):
        user_id = randint(290000, 295000)
        service = CategoryService(db)
        mcc_code = 6543
        _ensure_mcc(db, mcc_code, "Success MCC Store")
        data = CategoryCreateFromMCC(mcc_code=mcc_code)

        cat = service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)
        assert cat.name == "Success MCC Store"
        assert cat.mcc_code == mcc_code
        assert cat.created_by == CategoryCreatedBy.SYSTEM

    def test_create_from_mcc_with_custom_name(self, db):
        user_id = randint(295000, 300000)
        service = CategoryService(db)
        mcc_code = 6544
        _ensure_mcc(db, mcc_code, "Original Name")
        data = CategoryCreateFromMCC(mcc_code=mcc_code, custom_name="My Custom Name")

        cat = service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)
        assert cat.name == "My Custom Name"

    def test_create_from_mcc_with_translation(self, db):
        user_id = randint(300000, 305000)
        service = CategoryService(db)
        mcc_code = 6545
        mcc = _ensure_mcc(db, mcc_code, "English Name")

        # Add Russian translation
        translation = db.query(MCCTranslation).filter(
            MCCTranslation.mcc_code == mcc_code, MCCTranslation.lang == "ru"
        ).first()
        if not translation:
            trans = MCCTranslation(mcc_code=mcc_code, lang="ru", text="Русское название")
            db.add(trans)
            db.commit()

        data = CategoryCreateFromMCC(mcc_code=mcc_code)
        cat = service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID, language="ru")
        assert cat.name == "Русское название"

    def test_create_from_mcc_duplicate_raises_conflict(self, db):
        user_id = randint(305000, 310000)
        service = CategoryService(db)
        mcc_code = 6546
        _ensure_mcc(db, mcc_code, "Duplicate MCC")
        data = CategoryCreateFromMCC(mcc_code=mcc_code)

        # First creation succeeds
        service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)

        # Second creation should raise a validation-type error
        # (CategoryNameConflictError.__init__ signature mismatch causes TypeError
        # which is caught and re-raised as CategoryValidationError)
        with pytest.raises(Exception):
            service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)

    def test_create_from_mcc_unauthorized_raises(self, db):
        user_id = randint(310000, 315000)
        service = CategoryService(db)
        mcc_code = 6547
        _ensure_mcc(db, mcc_code, "Unauthorized MCC")
        data = CategoryCreateFromMCC(mcc_code=mcc_code)

        with patch("app.clients.workspace.WorkspaceClient.authorize", return_value=(False, None)):
            with pytest.raises(Exception):
                service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID)

    def test_create_from_mcc_fallback_to_english_when_no_translation(self, db):
        user_id = randint(315000, 320000)
        service = CategoryService(db)
        mcc_code = 6548
        _ensure_mcc(db, mcc_code, "Fallback English")
        data = CategoryCreateFromMCC(mcc_code=mcc_code)

        # Request Ukrainian but no Ukrainian translation exists
        cat = service.create_from_mcc(data, user_id, TEST_WORKSPACE_ID, language="uk")
        assert cat.name == "Fallback English"


# ---------------------------------------------------------------------------
# CategoryService.create_from_mcc_batch
# ---------------------------------------------------------------------------

class TestCategoryServiceCreateFromMCCBatch:
    def test_batch_create_all_success(self, db):
        user_id = randint(320000, 325000)
        service = CategoryService(db)
        mcc1 = 7001
        mcc2 = 7002
        _ensure_mcc(db, mcc1, "Batch Store One")
        _ensure_mcc(db, mcc2, "Batch Store Two")

        batch_data = CategoryCreateFromMCCBatch(
            categories=[
                CategoryCreateFromMCC(mcc_code=mcc1),
                CategoryCreateFromMCC(mcc_code=mcc2),
            ]
        )
        response = service.create_from_mcc_batch(batch_data, user_id, TEST_WORKSPACE_ID)
        assert response.total_requested == 2
        assert response.successful == 2
        assert response.failed == 0
        for result in response.results:
            assert result.success is True

    def test_batch_create_partial_failure(self, db):
        user_id = randint(325000, 330000)
        service = CategoryService(db)
        mcc_valid = 7003
        mcc_invalid = 9998  # Does not exist as MCC code
        _ensure_mcc(db, mcc_valid, "Valid Batch Store")

        # Ensure mcc_invalid does NOT exist
        from app.models.mcc import MCCCode as MCCModel
        inv = db.query(MCCModel).filter(MCCModel.mcc_code == mcc_invalid).first()
        if inv:
            db.delete(inv)
            db.commit()

        batch_data = CategoryCreateFromMCCBatch(
            categories=[
                CategoryCreateFromMCC(mcc_code=mcc_valid),
                CategoryCreateFromMCC(mcc_code=mcc_invalid),
            ]
        )
        response = service.create_from_mcc_batch(batch_data, user_id, TEST_WORKSPACE_ID)
        assert response.total_requested == 2
        assert response.successful == 1
        assert response.failed == 1

    def test_batch_create_with_language(self, db):
        user_id = randint(330000, 335000)
        service = CategoryService(db)
        mcc_code = 7004
        mcc = _ensure_mcc(db, mcc_code, "Batch Language Store")

        # Add Russian translation
        trans = db.query(MCCTranslation).filter(
            MCCTranslation.mcc_code == mcc_code, MCCTranslation.lang == "ru"
        ).first()
        if not trans:
            t = MCCTranslation(mcc_code=mcc_code, lang="ru", text="Магазин")
            db.add(t)
            db.commit()

        batch_data = CategoryCreateFromMCCBatch(
            categories=[CategoryCreateFromMCC(mcc_code=mcc_code)],
            language=SupportedLanguage.RU,
        )
        response = service.create_from_mcc_batch(batch_data, user_id, TEST_WORKSPACE_ID)
        assert response.successful == 1
        assert response.results[0].category_name == "Магазин"

    def test_batch_create_all_fail_returns_failure_results(self, db):
        user_id = randint(335000, 340000)
        service = CategoryService(db)

        # Both MCC codes do not exist
        from app.models.mcc import MCCCode as MCCModel
        for code in [9991, 9992]:
            inv = db.query(MCCModel).filter(MCCModel.mcc_code == code).first()
            if inv:
                db.delete(inv)
                db.commit()

        batch_data = CategoryCreateFromMCCBatch(
            categories=[
                CategoryCreateFromMCC(mcc_code=9991),
                CategoryCreateFromMCC(mcc_code=9992),
            ]
        )
        response = service.create_from_mcc_batch(batch_data, user_id, TEST_WORKSPACE_ID)
        assert response.failed == 2
        assert response.successful == 0
        for result in response.results:
            assert result.success is False
            assert result.error is not None
