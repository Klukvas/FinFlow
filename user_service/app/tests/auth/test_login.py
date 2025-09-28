from fastapi.testclient import TestClient
from fastapi import Response, status
import pytest
from app.exceptions.user_errors import UserServiceError


class TestLogin:

    def test_login_user(self, client: TestClient, user_data):
        client.post("/auth/register", json=user_data)

        # Login
        response = client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_login_user_with_invalid_password(self, client: TestClient, user_data):
        client.post("/auth/register", json=user_data)

        # Login
        response = client.post("/auth/login", json={
            "email": user_data["email"],
            "password": "invalid_password"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == UserServiceError.INVALID_CREDENTIALS
    
    def test_login_user_with_invalid_email(self, client: TestClient, user_data):
        client.post("/auth/register", json=user_data)

        # Login
        response = client.post("/auth/login", json={
            "email": "invalid_password@example.com",
            "password": user_data["password"]
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == UserServiceError.INVALID_CREDENTIALS
    def test_login_user_without_email_field(self, client: TestClient, user_data):
        client.post("/auth/register", json=user_data)

        # Login
        response = client.post("/auth/login", json={
            "password": user_data["password"]
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Email is required'}
    
    def test_login_user_without_password_field(self, client: TestClient, user_data):
        client.post("/auth/register", json=user_data)

        # Login
        response = client.post("/auth/login", json={
            "email": user_data["email"],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Password is required'}