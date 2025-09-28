from fastapi.testclient import TestClient
from fastapi import Response, status
from app.exceptions.user_errors import UserServiceError
import pytest
class TestRegistration:
    def test_register_user(self, client: TestClient, user_data):
        response: Response = client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    def test_register_user_with_existing_email(self, client: TestClient, user_data: dict, fake):
        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        user_data.update({"username": fake.unique.user_name()})

        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == UserServiceError.EMAIL_ALREADY_REGISTERED

    def test_register_user_with_existing_username(self, client: TestClient, user_data: dict, fake):
        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        user_data.update({"email": fake.unique.email()})

        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == UserServiceError.USERNAME_ALREADY_REGISTERED
    
    def test_register_user_without_email(self, client: TestClient, user_data: dict, fake):
        del user_data['email']
        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Email is required'}
    
    def test_register_user_without_username(self, client: TestClient, user_data: dict, fake):
        del user_data['username']
        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Username is required'}
    
    def test_register_user_without_password(self, client: TestClient, user_data: dict, fake):
        del user_data['password']
        response: Response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'error': 'Password is required'}

