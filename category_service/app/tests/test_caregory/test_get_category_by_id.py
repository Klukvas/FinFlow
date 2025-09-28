import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from starlette import status

class TestGetCategoryById:

    def test_get_category_by_id_success(self, client: TestClient, fake: Faker):
        user_id = randint(10**2, 10**3)
        name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            # Создаем категорию
            create_resp = client.post(
                "/categories/",
                json={"name": name},
                headers={"Authorization": "Bearer 123"}
            )
            category_id = create_resp.json()["id"]

            # Получаем категорию по id
            get_resp = client.get(
                f"/categories/{category_id}",
                headers={"Authorization": "Bearer 123"}
            )

        assert get_resp.status_code == status.HTTP_200_OK
        data = get_resp.json()
        assert data["id"] == category_id
        assert data["name"] == name

    def test_get_category_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)
        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get("/categories/99999", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"

    def test_get_category_not_owned(self, client: TestClient, fake: Faker):
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user1_id
            create_resp = client.post(
                "/categories/",
                json={"name": name},
                headers={"Authorization": "Bearer 123"}
            )
            category_id = create_resp.json()["id"]

            # Пытаемся получить от имени другого пользователя
            mock_decode.return_value = user2_id
            response = client.get(f"/categories/{category_id}", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"
