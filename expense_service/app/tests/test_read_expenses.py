import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from datetime import date
from starlette import status
import time


class TestReadExpenses:

    def test_get_expenses_empty(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get("/expenses/", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_expenses_with_data(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        subcategory_id = 10
        category_id = 20

        with patch("app.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_subcategory_and_category") as mock_validate:

            mock_decode.return_value = user_id
            mock_validate.return_value = {
                "user_id": user_id,
                "category_id": category_id
            }

            for _ in range(3):
                client.post(
                    "/expenses/",
                    json={
                        "amount": float(fake.pydecimal(left_digits=2, right_digits=2)),
                        "date": str(date.today()),
                        "subcategory_id": subcategory_id,
                        "category_id": category_id
                    },
                    headers={"Authorization": "Bearer 123"}
                )

            max_retries = 10
            response = client.get("/expenses/", headers={"Authorization": "Bearer 123"})
            data = response.json()
            for _ in range(max_retries):
                if len(data) == 3:
                    break
                time.sleep(0.05)
                response = client.get("/expenses/", headers={"Authorization": "Bearer 123"})
                data = response.json()

        assert len(data) == 3
        for expense in data:
            assert expense["user_id"] == user_id
            assert expense["subcategory_id"] == subcategory_id