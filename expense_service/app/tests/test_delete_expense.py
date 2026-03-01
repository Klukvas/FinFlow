import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from datetime import date
from starlette import status

WORKSPACE_HEADER = {"X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}


class TestDeleteExpense:

    def test_delete_expense_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        category_id = 20

        with patch("shared.auth.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:
            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            # Создаем расход
            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 120,
                    "date": str(date.today()),
                    "category_id": category_id,
                    "description": "Groceries"
                },
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            expense_id = create_resp.json()["id"]

            # Удаляем
            delete_resp = client.delete(
                f"/expenses/{expense_id}",
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_expense_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.delete(
                "/expenses/99999",
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_expense_not_owned(self, client: TestClient, fake: Faker):
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        category_id = 20

        with patch("shared.auth.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:
            mock_decode.return_value = user1_id
            mock_validate.return_value = {"user_id": user1_id, "category_id": category_id}

            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 75,
                    "date": str(date.today()),
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            expense_id = create_resp.json()["id"]

            mock_decode.return_value = user2_id
            response = client.delete(
                f"/expenses/{expense_id}",
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
