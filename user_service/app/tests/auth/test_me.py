from fastapi.testclient import TestClient
from fastapi import Response, status
from app.exceptions.user_errors import UserServiceError


class TestGetMe:

    def test_get_me_successfully(self, client: TestClient, user_data):
        # Register and login
        register_response = client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]

        # Get current user
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data

    def test_get_me_with_invalid_token(self, client: TestClient):
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid.token.value"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == UserServiceError.INVALID_TOKEN