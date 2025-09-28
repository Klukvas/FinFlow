from fastapi.testclient import TestClient
from fastapi import status
import pytest
from unittest.mock import patch
from random import randint
from faker import Faker


class TestGetAllCategories:
    def test_get_all_categories_returns_created(self, client: TestClient, fake: Faker):
        user_id = randint(10**2, 10**3)
        categories = [fake.word() for _ in range(3)]

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            for name in categories:
                client.post(
                    "/categories/",
                    json={"name": name},
                    headers={"Authorization": "Bearer 123"}
                )

            response = client.get(
                "/categories/",
                headers={"Authorization": "Bearer 123"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(categories)
        assert sorted([c["name"] for c in data]) == sorted(categories)

    def test_get_all_categories_returns_empty_for_new_user(self, client: TestClient):
        user_id = randint(10**4, 10**5)
        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get("/categories/", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_all_categories_does_not_leak_other_users(self, client: TestClient, fake: Faker):
        user1_id = randint(10**2, 10**3)
        user2_id = randint(10**3, 10**4)
        user1_categories = [fake.word() for _ in range(2)]
        user2_categories = [fake.word() for _ in range(2)]

        with patch("app.dependencies.decode_token") as mock_decode:
            # Создаем категории от имени user1
            mock_decode.return_value = user1_id
            for name in user1_categories:
                client.post("/categories/", json={"name": name}, headers={"Authorization": "Bearer 123"})

            # Создаем категории от имени user2
            mock_decode.return_value = user2_id
            for name in user2_categories:
                client.post("/categories/", json={"name": name}, headers={"Authorization": "Bearer 123"})

            # Получаем категории только user1
            mock_decode.return_value = user1_id
            response = client.get("/categories/", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert sorted([c["name"] for c in data]) == sorted(user1_categories)
        assert not any(name in [c["name"] for c in data] for name in user2_categories)
