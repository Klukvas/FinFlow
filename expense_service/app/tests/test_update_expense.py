

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from datetime import date
from faker import Faker
from starlette import status

WORKSPACE_HEADER = {"X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}


class TestUpdateExpense:

    def test_update_expense_success_amount_and_description(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        category_id = 20

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:
            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            # Создание расхода
            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 100,
                    "date": str(date.today()),
                    "category_id": category_id,
                    "description": "Lunch"
                },
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            expense_id = create_resp.json()["id"]

            # Обновление
            new_amount = 200
            new_description = "Dinner"
            update_resp = client.patch(
                f"/expenses/{expense_id}",
                json={"amount": new_amount, "description": new_description},
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
        assert update_resp.status_code == status.HTTP_200_OK
        data = update_resp.json()
        assert data["amount"] == new_amount
        assert data["description"] == new_description


    def test_update_expense_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.patch(
                "/expenses/99999",
                json={"amount": 300},
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_update_expense_not_owned(self, client: TestClient, fake: Faker):
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        category_id = 20

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:
            mock_decode.return_value = user1_id
            mock_validate.return_value = {"user_id": user1_id, "category_id": category_id}

            # Создание расхода от user1
            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 100,
                    "date": str(date.today()),
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            expense_id = create_resp.json()["id"]

            # Попытка обновить от user2
            mock_decode.return_value = user2_id
            response = client.patch(
                f"/expenses/{expense_id}",
                json={"amount": 500},
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_update_expense_with_new_category_validation(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        category_id = 20
        new_category_id = 30

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:
            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 50,
                    "date": str(date.today()),
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            expense_id = create_resp.json()["id"]

            # Эмулируем успешную валидацию новой категории
            mock_validate.return_value = {"user_id": user_id, "category_id": new_category_id}

            response = client.patch(
                f"/expenses/{expense_id}",
                json={"category_id": new_category_id},
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["category_id"] == new_category_id
