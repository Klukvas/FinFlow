

from fastapi.testclient import TestClient
from unittest.mock import patch
from random import randint
from faker import Faker
from starlette import status

class TestDeleteCategory:

    def test_delete_category_success(self, client: TestClient, fake: Faker):
        user_id = randint(1000, 2000)
        name = fake.word()

        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            create_resp = client.post(
                "/categories/",
                json={"name": name},
                headers={"Authorization": "Bearer 123"}
            )
            category_id = create_resp.json()["id"]

            delete_resp = client.delete(
                f"/categories/{category_id}",
                headers={"Authorization": "Bearer 123"}
            )

        assert delete_resp.status_code == status.HTTP_200_OK

    def test_delete_category_not_found(self, client: TestClient):
        user_id = randint(1000, 2000)
        with patch("app.dependencies.decode_token") as mock_decode:
            mock_decode.return_value = user_id
            response = client.delete("/categories/99999", headers={"Authorization": "Bearer 123"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"

    def test_delete_category_not_owned(self, client: TestClient, fake: Faker):
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

            mock_decode.return_value = user2_id
            response = client.delete(
                f"/categories/{category_id}",
                headers={"Authorization": "Bearer 123"}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Category not found"