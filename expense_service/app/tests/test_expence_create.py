

from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch
from random import randint
from faker import Faker
from starlette import status


class TestCreateExpense:

    def test_create_expense_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        category_id = 456  # должен быть мокан
        payload = {
            "amount": 99.99,
            "date": "2025-04-12",
            "category_id": category_id
        }

        with patch("shared.auth.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:

            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            response = client.post(
                "/expenses/",
                json=payload,
                headers={"Authorization": "Bearer 123", "X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == payload["amount"]
        assert data["category_id"] == category_id

    def test_create_expense_category_not_found(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        payload = {
            "amount": 49.50,
            "date": "2025-04-12",
            "category_id": 999
        }

        with patch("shared.auth.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:

            mock_decode.return_value = user_id
            mock_validate.side_effect = HTTPException(status_code=404, detail="Category does not exist")

            response = client.post(
                "/expenses/",
                json=payload,
                headers={"Authorization": "Bearer 123", "X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}
            )

        # Category validation errors are wrapped as ExternalServiceError (503)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Category does not exist" in response.json()["error"]
