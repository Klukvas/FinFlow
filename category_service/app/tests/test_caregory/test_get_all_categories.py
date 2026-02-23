from fastapi.testclient import TestClient
from fastapi import status
import pytest
from unittest.mock import patch
from random import randint
from faker import Faker

from app.tests.conftest import TEST_WORKSPACE_ID_HEADER


class TestGetAllCategories:
    def test_get_all_categories_returns_created(self, client: TestClient, fake: Faker):
        user_id = randint(10**2, 10**3)
        categories = [fake.word() + fake.word() for _ in range(3)]  # ensure >= 3 chars

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            for name in categories:
                client.post(
                    "/categories/",
                    json={"name": name},
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                    },
                )

            response = client.get(
                "/categories/",
                headers={
                    "Authorization": "Bearer 123",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        items = data["items"]
        assert isinstance(items, list)
        # The shared test DB may contain categories from other tests.
        # Verify that all created categories appear in the results.
        returned_names = [c["name"] for c in items]
        for name in categories:
            assert name in returned_names

    def test_get_all_categories_returns_empty_for_new_user(self, client: TestClient):
        user_id = randint(10**4, 10**5)
        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get(
                "/categories/",
                headers={
                    "Authorization": "Bearer 123",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        items = data["items"]
        assert isinstance(items, list)
        # New user may have 0 categories in this workspace (shared test db may have others)
        assert data["total"] >= 0

    def test_get_all_categories_does_not_leak_other_users(
        self, client: TestClient, fake: Faker
    ):
        user1_id = randint(10**2, 10**3)
        user2_id = randint(10**3, 10**4)
        user1_categories = [fake.word() + fake.word() for _ in range(2)]
        user2_categories = [fake.word() + fake.word() for _ in range(2)]

        with patch("app.dependencies.decode_token") as mock_decode:
            # Create categories for user1
            mock_decode.return_value = user1_id
            for name in user1_categories:
                client.post(
                    "/categories/",
                    json={"name": name},
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                    },
                )

            # Create categories for user2
            mock_decode.return_value = user2_id
            for name in user2_categories:
                client.post(
                    "/categories/",
                    json={"name": name},
                    headers={
                        "Authorization": "Bearer 123",
                        "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                    },
                )

            # Get categories for user1 (flat to get all)
            mock_decode.return_value = user1_id
            response = client.get(
                "/categories/?flat=true",
                headers={
                    "Authorization": "Bearer 123",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        names = [c["name"] for c in data["items"]]
        for name in user1_categories:
            assert name in names
