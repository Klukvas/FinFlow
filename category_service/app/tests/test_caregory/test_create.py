from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from random import randint
from faker import Faker

from app.tests.conftest import TEST_WORKSPACE_ID_HEADER


class TestCreateCategory:

    def test_create_category(self, client: TestClient, fake: Faker):
        user_id = randint(10**2, 10**3)
        category_name = fake.word() + fake.word()  # ensure >= 3 chars

        with patch("shared.auth.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.post(
                "/categories/",
                json={"name": category_name},
                headers={
                    "Authorization": "Bearer 123",
                    "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
                },
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == category_name
        assert data["user_id"] == user_id
        assert "id" in data

    @patch("shared.auth.dependencies.decode_token", return_value=123)
    def test_create_category_missing_name(self, mock_decode, client: TestClient):
        response = client.post(
            "/categories/",
            json={},
            headers={
                "Authorization": "Bearer 123",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Name" in response.json()["error"]

    @patch("shared.auth.dependencies.decode_token", return_value=123)
    def test_create_category_empty_name(self, mock_decode, client: TestClient):
        response = client.post(
            "/categories/",
            json={"name": ""},
            headers={
                "Authorization": "Bearer 123",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_category_unauthorized(self, client: TestClient):
        response = client.post("/categories/", json={"name": "Unauthorized"})
        assert response.status_code == 403
