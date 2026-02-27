"""
Tests for app/routers/internal.py - internal API endpoints.
Covers: get_category_internal, get_mcc_codes_internal, get_default_categories_internal,
        check_category_exists_by_mcc, check_categories_exist_by_mcc_batch, get_category_by_mcc
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from random import randint
from uuid import UUID

from app.tests.conftest import TEST_WORKSPACE_ID_HEADER, TEST_WORKSPACE_ID

INTERNAL_TOKEN = "test-internal-token"
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_TOKEN}


class TestGetCategoryInternal:
    """Tests for GET /internal/categories/{category_id}"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get(
            "/internal/categories/1?user_id=1&workspace_id=" + TEST_WORKSPACE_ID_HEADER
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_internal_token_returns_403(self, client: TestClient):
        response = client.get(
            "/internal/categories/1?user_id=1&workspace_id=" + TEST_WORKSPACE_ID_HEADER,
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_existing_category(self, client: TestClient, fake):
        user_id = randint(5000, 6000)
        name = fake.word() + fake.word()

        with patch("shared.auth.dependencies.decode_token", return_value=user_id):
            create_resp = client.post(
                "/categories/",
                json={"name": name},
                headers={
                    "Authorization": "Bearer test",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )
        assert create_resp.status_code == status.HTTP_201_CREATED
        category_id = create_resp.json()["id"]

        response = client.get(
            f"/internal/categories/{category_id}?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == name
        assert data["user_id"] == user_id

    def test_get_nonexistent_category_returns_error(self, client: TestClient):
        """get_by_id_internal wraps not-found as CategoryValidationError (400),
        which the router then catches and re-raises as 500."""
        response = client.get(
            f"/internal/categories/999999?user_id=1&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_invalid_workspace_id_format_returns_error(self, client: TestClient):
        """The HTTPException(400) raised for invalid UUID format is caught by
        the outer except Exception and re-raised as 500."""
        response = client.get(
            "/internal/categories/1?user_id=1&workspace_id=not-a-uuid",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_category_belongs_to_different_user_returns_error(self, client: TestClient, fake):
        user1_id = randint(6000, 7000)
        user2_id = randint(7000, 8000)
        name = fake.word() + fake.word()

        with patch("shared.auth.dependencies.decode_token", return_value=user1_id):
            create_resp = client.post(
                "/categories/",
                json={"name": name},
                headers={
                    "Authorization": "Bearer test",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )
        category_id = create_resp.json()["id"]

        response = client.get(
            f"/internal/categories/{category_id}?user_id={user2_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        # The router's outer except catches ownership errors and returns 500
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class TestGetMCCCodesInternal:
    """Tests for GET /internal/mcc/codes"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get("/internal/mcc/codes")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_mcc_codes_english(self, client: TestClient):
        response = client.get(
            "/internal/mcc/codes?language=en",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "language" in data
        assert isinstance(data["items"], list)

    def test_get_mcc_codes_russian(self, client: TestClient):
        response = client.get(
            "/internal/mcc/codes?language=ru",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_mcc_codes_ukrainian(self, client: TestClient):
        response = client.get(
            "/internal/mcc/codes?language=uk",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_mcc_codes_default_language(self, client: TestClient):
        response = client.get(
            "/internal/mcc/codes",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK


class TestGetDefaultCategoriesInternal:
    """Tests for GET /internal/mcc/defaults"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get("/internal/mcc/defaults")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_default_categories_english(self, client: TestClient):
        response = client.get(
            "/internal/mcc/defaults?language=en",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_default_categories_russian(self, client: TestClient):
        response = client.get(
            "/internal/mcc/defaults?language=ru",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    def test_get_default_categories_ukrainian(self, client: TestClient):
        response = client.get(
            "/internal/mcc/defaults?language=uk",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_default_categories_default_language(self, client: TestClient):
        response = client.get(
            "/internal/mcc/defaults",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK


class TestCheckCategoryExistsByMCC:
    """Tests for GET /internal/categories/check-mcc/{mcc_code}"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/categories/check-mcc/5411?user_id=1&workspace_id={TEST_WORKSPACE_ID_HEADER}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_category_does_not_exist(self, client: TestClient):
        user_id = randint(20000, 25000)
        response = client.get(
            f"/internal/categories/check-mcc/5411?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "exists" in data
        assert data["exists"] is False

    def test_invalid_workspace_id_returns_error(self, client: TestClient):
        """Bad UUID is caught by outer except and turned into 500."""
        response = client.get(
            "/internal/categories/check-mcc/5411?user_id=1&workspace_id=bad-uuid",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_category_exists_after_creation(self, client: TestClient, db):
        """Create a category with mcc_code and then check it exists."""
        from app.models.category import Category, CategoryType as ModelCategoryType
        from uuid import UUID

        user_id = randint(25000, 30000)
        mcc_code = 5411

        # Seed MCC code if needed and create category directly in DB
        from app.models.mcc import MCCCode
        existing_mcc = db.query(MCCCode).filter(MCCCode.mcc_code == mcc_code).first()
        if not existing_mcc:
            mcc = MCCCode(mcc_code=mcc_code, name="Grocery Stores", is_default=True)
            db.add(mcc)
            db.commit()

        cat = Category(
            name="GroceryTest",
            user_id=user_id,
            workspace_id=TEST_WORKSPACE_ID,
            mcc_code=mcc_code,
            type=ModelCategoryType.EXPENSE,
        )
        db.add(cat)
        db.commit()

        response = client.get(
            f"/internal/categories/check-mcc/{mcc_code}?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["exists"] is True


class TestCheckCategoriesExistByMCCBatch:
    """Tests for POST /internal/categories/check-mcc-batch"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={"mcc_codes": [5411], "user_id": 1, "workspace_id": TEST_WORKSPACE_ID_HEADER},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_batch_check_returns_results(self, client: TestClient):
        user_id = randint(30000, 35000)
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={
                "mcc_codes": [5411, 5812, 4121],
                "user_id": user_id,
                "workspace_id": TEST_WORKSPACE_ID_HEADER,
            },
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        for result in data["results"]:
            assert "mcc_code" in result
            assert "exists" in result
            assert "category_id" in result

    def test_missing_mcc_codes_returns_error(self, client: TestClient):
        """HTTPException(400) raised inside try block is caught by outer except -> 500."""
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={"user_id": 1, "workspace_id": TEST_WORKSPACE_ID_HEADER},
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_missing_user_id_returns_error(self, client: TestClient):
        """HTTPException(400) raised inside try block is caught by outer except -> 500."""
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={"mcc_codes": [5411], "workspace_id": TEST_WORKSPACE_ID_HEADER},
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_missing_workspace_id_returns_error(self, client: TestClient):
        """HTTPException(400) raised inside try block is caught by outer except -> 500."""
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={"mcc_codes": [5411], "user_id": 1},
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_invalid_workspace_id_format_returns_error(self, client: TestClient):
        """Bad UUID triggers HTTPException(400) which is caught by outer except as 500."""
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={
                "mcc_codes": [5411],
                "user_id": 1,
                "workspace_id": "not-a-uuid",
            },
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_empty_mcc_codes_list_returns_error(self, client: TestClient):
        """Empty mcc_codes raises HTTPException(400) caught by outer except -> 500."""
        response = client.post(
            "/internal/categories/check-mcc-batch",
            json={
                "mcc_codes": [],
                "user_id": 1,
                "workspace_id": TEST_WORKSPACE_ID_HEADER,
            },
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class TestGetCategoryByMCC:
    """Tests for GET /internal/categories/get-by-mcc/{mcc_code}"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get(
            f"/internal/categories/get-by-mcc/5411?user_id=1&workspace_id={TEST_WORKSPACE_ID_HEADER}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_category_not_found_returns_not_exists(self, client: TestClient):
        user_id = randint(35000, 40000)
        response = client.get(
            f"/internal/categories/get-by-mcc/5411?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is False
        assert data["category_id"] is None

    def test_invalid_workspace_id_returns_error(self, client: TestClient):
        """Bad UUID is caught by outer except and turned into 500."""
        response = client.get(
            "/internal/categories/get-by-mcc/5411?user_id=1&workspace_id=bad-uuid",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_category_found_returns_exists_with_id(self, client: TestClient, db):
        from app.models.category import Category, CategoryType as ModelCategoryType
        from app.models.mcc import MCCCode

        user_id = randint(40000, 45000)
        mcc_code = 5812

        existing_mcc = db.query(MCCCode).filter(MCCCode.mcc_code == mcc_code).first()
        if not existing_mcc:
            mcc = MCCCode(mcc_code=mcc_code, name="Eating Places, Restaurants", is_default=True)
            db.add(mcc)
            db.commit()

        cat = Category(
            name="RestaurantTest",
            user_id=user_id,
            workspace_id=TEST_WORKSPACE_ID,
            mcc_code=mcc_code,
            type=ModelCategoryType.EXPENSE,
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)

        response = client.get(
            f"/internal/categories/get-by-mcc/{mcc_code}?user_id={user_id}&workspace_id={TEST_WORKSPACE_ID_HEADER}",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is True
        assert data["category_id"] == cat.id
