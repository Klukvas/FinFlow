"""
Test file demonstrating the improved expense service functionality
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from app.main import app
from app.exceptions import (
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError
)

client = TestClient(app)

class TestImprovedExpenseService:
    """Test improved expense service functionality"""

    @patch("app.dependencies.decode_token")
    @patch("app.clients.category_service_client.CategoryServiceClient.validate_category")
    def test_create_expense_with_validation(self, mock_validate, mock_decode):
        """Test expense creation with improved validation"""
        mock_decode.return_value = 1
        mock_validate.return_value = {"id": 1, "name": "Food", "user_id": 1}
        
        # Test valid expense creation
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "description": "Lunch at restaurant",
                "date": "2024-01-15"
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 25.50
        assert data["category_id"] == 1
        assert data["user_id"] == 1

    @patch("app.dependencies.decode_token")
    def test_create_expense_with_invalid_amount(self, mock_decode):
        """Test expense creation with invalid amount"""
        mock_decode.return_value = 1
        
        # Test negative amount
        response = client.post(
            "/expenses/",
            json={"amount": -10.0, "category_id": 1},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "Amount must be greater than 0" in response.json()["error"]

        # Test zero amount
        response = client.post(
            "/expenses/",
            json={"amount": 0, "category_id": 1},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "Amount must be greater than 0" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    def test_create_expense_with_invalid_description(self, mock_decode):
        """Test expense creation with invalid description"""
        mock_decode.return_value = 1
        
        # Test description too long
        long_description = "x" * 501
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "description": long_description
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "exceeds maximum length" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    def test_create_expense_with_future_date(self, mock_decode):
        """Test expense creation with future date"""
        mock_decode.return_value = 1
        
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "date": future_date
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "cannot be in the future" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    @patch("app.clients.category_service_client.CategoryServiceClient.validate_category")
    def test_create_expense_with_category_validation(self, mock_validate, mock_decode):
        """Test expense creation with category validation"""
        mock_decode.return_value = 1
        mock_validate.side_effect = HTTPException(status_code=400, detail="Category does not exist")
        
        response = client.post(
            "/expenses/",
            json={"amount": 25.50, "category_id": 999},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
        assert "Category does not exist" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    @patch("app.clients.category_service_client.CategoryServiceClient.validate_category")
    def test_update_expense_with_validation(self, mock_validate, mock_decode):
        """Test expense update with validation"""
        mock_decode.return_value = 1
        mock_validate.return_value = {"id": 1, "name": "Food", "user_id": 1}
        
        # First create an expense
        create_response = client.post(
            "/expenses/",
            json={"amount": 25.50, "category_id": 1},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert create_response.status_code == 201
        expense_id = create_response.json()["id"]
        
        # Update the expense
        response = client.patch(
            f"/expenses/{expense_id}",
            json={"amount": 30.00, "description": "Updated lunch"},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 30.00
        assert data["description"] == "Updated lunch"

    @patch("app.dependencies.decode_token")
    def test_get_expense_not_found(self, mock_decode):
        """Test getting non-existent expense"""
        mock_decode.return_value = 1
        
        response = client.get(
            "/expenses/999",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 404
        assert "Expense with ID 999 not found" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    @patch("app.clients.category_service_client.CategoryServiceClient.validate_category")
    def test_get_expenses_by_category(self, mock_validate, mock_decode):
        """Test getting expenses by category"""
        mock_decode.return_value = 1
        mock_validate.return_value = {"id": 1, "name": "Food", "user_id": 1}
        
        # Create some expenses
        client.post(
            "/expenses/",
            json={"amount": 25.50, "category_id": 1},
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Get expenses by category
        response = client.get(
            "/expenses/category/1",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    @patch("app.dependencies.decode_token")
    @patch("app.clients.category_service_client.CategoryServiceClient.validate_category")
    def test_get_expenses_by_date_range(self, mock_validate, mock_decode):
        """Test getting expenses by date range"""
        mock_decode.return_value = 1
        mock_validate.return_value = {"id": 1, "name": "Food", "user_id": 1}
        
        # Create an expense with specific date
        client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "date": "2024-01-15"
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Get expenses by date range
        response = client.get(
            "/expenses/date-range/?start_date=2024-01-01&end_date=2024-01-31",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_unauthorized_access(self):
        """Test unauthorized access handling"""
        # Test without authorization header
        response = client.get("/expenses/")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["error"]
        
        # Test with invalid token format
        response = client.get(
            "/expenses/",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401
        assert "Invalid token format" in response.json()["error"]

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "expense-service"

    @patch("app.dependencies.decode_token")
    def test_amount_precision_handling(self, mock_decode):
        """Test amount precision handling"""
        mock_decode.return_value = 1
        
        # Test amount with many decimal places
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.555555,
                "category_id": 1
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        # Should round to 2 decimal places
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 25.56

    @patch("app.dependencies.decode_token")
    def test_description_whitespace_handling(self, mock_decode):
        """Test description whitespace handling"""
        mock_decode.return_value = 1
        
        # Test description with extra whitespace
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "description": "  Lunch at restaurant  "
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Lunch at restaurant"  # Should be trimmed

    @patch("app.dependencies.decode_token")
    def test_empty_description_handling(self, mock_decode):
        """Test empty description handling"""
        mock_decode.return_value = 1
        
        # Test empty description
        response = client.post(
            "/expenses/",
            json={
                "amount": 25.50,
                "category_id": 1,
                "description": "   "  # Only whitespace
            },
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None  # Should be converted to None
