import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from datetime import date
from starlette import status


class TestReadSingleExpense:

    def test_get_expense_by_id_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        subcategory_id = 123
        category_id = 456
        amount = float(fake.pydecimal(left_digits=2, right_digits=2))

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_subcategory_and_category") as mock_validate:

            mock_decode.return_value = user_id
            mock_validate.return_value = {"user_id": user_id, "category_id": category_id}

            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": amount,
                    "date": str(date.today()),
                    "subcategory_id": subcategory_id,
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123"}
            )

            expense_id = create_resp.json()["id"]
            response = client.get(f"/expenses/{expense_id}", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == expense_id
        assert data["user_id"] == user_id
        assert data["amount"] == amount

    def test_get_expense_by_id_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get("/expenses/99999", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Expense not found"

    def test_get_expense_by_id_not_owned(self, client: TestClient, fake: Faker):
        user1_id = randint(1000, 2000)
        user2_id = randint(2000, 3000)
        subcategory_id = 123
        category_id = 456
        amount = float(fake.pydecimal(left_digits=2, right_digits=2, positive=True))

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_subcategory_and_category") as mock_validate:

            mock_decode.return_value = user1_id
            mock_validate.return_value = {"user_id": user1_id, "category_id": category_id}

            create_resp = client.post(
                "/expenses/",
                json={
                    "amount": amount,
                    "date": str(date.today()),
                    "subcategory_id": subcategory_id,
                    "category_id": category_id
                },
                headers={"Authorization": "Bearer 123"}
            )
            expense_id = create_resp.json()["id"]

            mock_decode.return_value = user2_id
            response = client.get(f"/expenses/{expense_id}", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == 'Expense not found'
