import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from datetime import date
from starlette import status

class TestDeleteExpense:

    def test_delete_expense_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        subcategory_id = 10
        category_id = 20

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_subcategory_and_category") as mock_validate:
            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            # Создаем расход
            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 120,
                    "date": str(date.today()),
                    "subcategory_id": subcategory_id,
                    "category_id": category_id,
                    "description": "Groceries"
                },
                headers={"Authorization": "Bearer 123"}
            )
            expense_id = create_resp.json()["id"]

            # Удаляем
            delete_resp = client.delete(f"/expenses/{expense_id}", headers={"Authorization": "Bearer 123"})
            assert delete_resp.status_code == status.HTTP_200_OK

    def test_delete_expense_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.delete("/expenses/99999", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Expense not found"

    def test_delete_expense_not_owned(self, client: TestClient, fake: Faker):
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        subcategory_id = 10
        category_id = 20

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_subcategory_and_category") as mock_validate:
            mock_decode.return_value = user1_id
            mock_validate.return_value = {"user_id": user1_id, "category_id": category_id}

            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": 75,
                    "date": str(date.today()),
                    "subcategory_id": subcategory_id,
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123"}
            )
            expense_id = create_resp.json()["id"]

            mock_decode.return_value = user2_id
            response = client.delete(f"/expenses/{expense_id}", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
