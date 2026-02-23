"""
Test file demonstrating the improved user service functionality
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch
from app.main import app

client = TestClient(app)

class TestImprovedUserService:
    """Test improved user service functionality"""

    def test_register_user_with_validation(self):
        """Test user registration with comprehensive validation"""
        # Test valid registration
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_register_user_with_weak_password(self):
        """Test registration with weak password"""
        # Test password without uppercase letters
        response = client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "password": "weakpass123"  # No uppercase characters
            }
        )
        assert response.status_code == 400
        assert "uppercase" in response.json()["error"]

        # Test password too short
        response = client.post(
            "/auth/register",
            json={
                "email": "test3@example.com",
                "password": "Weak1!"  # Too short
            }
        )
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["error"]

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!"
            }
        )

        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["error"]

    def test_login_success(self):
        """Test successful login"""
        # First register a user
        client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!"
            }
        )
        
        # Then login
        response = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["error"]

    def test_get_current_user(self):
        """Test getting current user information"""
        # Register and login
        register_response = client.post(
            "/auth/register",
            json={
                "email": "current@example.com",
                "password": "SecurePass123!"
            }
        )
        token = register_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert "id" in data

    def test_get_current_user_unauthorized(self):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["error"]

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["error"]

    def test_update_user_information(self):
        """Test updating user information"""
        # Register and login
        register_response = client.post(
            "/auth/register",
            json={
                "email": "update@example.com",
                "password": "SecurePass123!"
            }
        )
        token = register_response.json()["access_token"]

        # Update user information
        response = client.put(
            "/auth/me",
            json={
                "email": "updated@example.com",
                "base_currency": "EUR"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    def test_change_password(self):
        """Test changing password"""
        # Register and login
        register_response = client.post(
            "/auth/register",
            json={
                "email": "changepass@example.com",
                "password": "OldPass123!"
            }
        )
        token = register_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/auth/change-password",
            json={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["detail"]

    def test_change_password_wrong_current(self):
        """Test changing password with wrong current password"""
        # Register and login
        register_response = client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "OldPass123!"
            }
        )
        token = register_response.json()["access_token"]
        
        # Try to change password with wrong current password
        response = client.post(
            "/auth/change-password",
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert "Current password is incorrect" in response.json()["error"]

    def test_change_password_weak_new_password(self):
        """Test changing password with weak new password"""
        # Register and login
        register_response = client.post(
            "/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "OldPass123!"
            }
        )
        token = register_response.json()["access_token"]
        
        # Try to change password with weak new password
        response = client.post(
            "/auth/change-password",
            json={
                "current_password": "OldPass123!",
                "new_password": "weak"  # Too weak
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["error"]

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-service"

    def test_validation_error_messages(self):
        """Test improved validation error messages"""
        # Test missing required fields
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com"
                # Missing password
            }
        )
        assert response.status_code == 400
        assert "Password is required" in response.json()["error"]

    def test_password_validation_comprehensive(self):
        """Test comprehensive password validation"""
        test_cases = [
            ("nouppercase1!", "Password must contain at least one uppercase letter"),
            ("NOLOWERCASE1!", "Password must contain at least one lowercase letter"),
            ("NoNumbers!", "Password must contain at least one number"),
            ("noupperalso1!", "Password must contain at least one uppercase letter"),
            ("Short1!", "Password must be at least 8 characters long"),
        ]
        
        for i, (password, expected_error) in enumerate(test_cases):
            response = client.post(
                "/auth/register",
                json={
                    "email": f"test{i+10}@example.com",
                    "password": password
                }
            )
            assert response.status_code == 400
            assert expected_error in response.json()["error"]

    def test_token_expiration_handling(self):
        """Test token expiration handling"""
        # This would require mocking time or using expired tokens
        # For now, just test that the endpoint exists
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["error"]

