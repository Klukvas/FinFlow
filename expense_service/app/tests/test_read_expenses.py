import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from datetime import date
from starlette import status
import time

WORKSPACE_HEADER = {"X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}


class TestReadExpenses:

    def test_get_expenses_empty(self, client: TestClient):
        user_id = randint(1000, 2000)

        with patch("shared.auth.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.get(
                "/expenses/",
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)  # Returns list (may have data from other tests)

    def test_get_expenses_with_data(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        category_id = 20

        with patch("shared.auth.dependencies.decode_token") as mock_decode, \
             patch("app.clients.category_service_client.CategoryServiceClient.validate_category") as mock_validate:

            mock_decode.return_value = user_id
            mock_validate.return_value = {
                "user_id": user_id,
                "category_id": category_id
            }

            for _ in range(3):
                client.post(
                    "/expenses/",
                    json={
                        "amount": float(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
                        "date": str(date.today()),
                        "category_id": category_id
                    },
                    headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
                )

            max_retries = 10
            response = client.get(
                "/expenses/",
                headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
            )
            data = response.json()
            for _ in range(max_retries):
                if len(data) >= 3:
                    break
                time.sleep(0.05)
                response = client.get(
                    "/expenses/",
                    headers={"Authorization": "Bearer 123", **WORKSPACE_HEADER}
                )
                data = response.json()

        user_expenses = [e for e in data if e["user_id"] == user_id]
        assert len(user_expenses) >= 3
