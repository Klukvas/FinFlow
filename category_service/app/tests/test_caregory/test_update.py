import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from starlette import status

class TestUpdateCategory:

    def test_update_category_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        original_name = fake.word()
        new_name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            create_resp = client.post(
                "/categories/",
                json={"name": original_name},
                headers={"Authorization": "Bearer 123"}
            )
            category_id = create_resp.json()["id"]

            update_resp = client.put(
                f"/categories/{category_id}",
                json={"name": new_name},
                headers={"Authorization": "Bearer 123"}
            )

        assert update_resp.status_code == status.HTTP_200_OK
        data = update_resp.json()
        assert data["id"] == category_id
        assert data["name"] == new_name

    def test_update_category_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)
        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.put(
                "/categories/99999",
                json={"name": "NewName"},
                headers={"Authorization": "Bearer 123"}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"

    def test_update_category_not_owned(self, client: TestClient, fake: Faker):
        
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        original_name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user1_id
            create_resp = client.post(
                "/categories/",
                json={"name": original_name},
                headers={"Authorization": "Bearer 123"}
            )
            category_id = create_resp.json()["id"]

            mock_decode.return_value = user2_id
            response = client.put(
                f"/categories/{category_id}",
                json={"name": "HackedName"},
                headers={"Authorization": "Bearer 123"}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"
