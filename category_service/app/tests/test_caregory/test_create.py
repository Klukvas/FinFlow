from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from random import randint
from faker import Faker


class TestCreateCategory:

    def test_create_category(self, client: TestClient, fake: Faker):
        user_id = randint(10**2, 10**3)
        category_name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.post(
                "/categories/", 
                json={"name": category_name}, 
                headers={"Authorization": "Bearer 123"}
            )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {'name': category_name, 'id': 1, 'user_id': user_id}

    @patch("app.dependencies.decode_token", return_value=123)
    def test_create_category_missing_name(self, mock_decode, client: TestClient):
        response = client.post("/categories/", json={}, headers={"Authorization": "Bearer 123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Name is required'}

    @patch("app.dependencies.decode_token", return_value=123)
    def test_create_category_empty_name(self, mock_decode, client: TestClient):
        response = client.post("/categories/", json={"name": ""}, headers={"Authorization": "Bearer 123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Name is required'}


    def test_create_category_unauthorized(self, client: TestClient):
        response = client.post("/categories/", json={"name": "Unauthorized"})
        assert response.status_code == 401