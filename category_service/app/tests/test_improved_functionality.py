"""
Test file demonstrating the improved category service functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError,
    CategoryOwnershipError
)
from app.tests.conftest import TEST_WORKSPACE_ID_HEADER

client = TestClient(app, raise_server_exceptions=False)


class TestImprovedCategoryService:
    """Test improved category service functionality"""

    @patch("app.dependencies.decode_token")
    def test_create_category_with_validation(self, mock_decode):
        """Test category creation with improved validation"""
        mock_decode.return_value = 1

        # Test valid category creation
        response = client.post(
            "/categories/",
            json={"name": "Food & Dining", "parent_id": None},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Food & Dining"
        assert data["user_id"] == 1

    @patch("app.dependencies.decode_token")
    def test_create_category_with_invalid_name(self, mock_decode):
        """Test category creation with invalid name"""
        mock_decode.return_value = 1

        # Test empty name
        response = client.post(
            "/categories/",
            json={"name": ""},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 400

        # Test name too short
        response = client.post(
            "/categories/",
            json={"name": "AB"},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 400
        assert "must be at least 3 characters long" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    def test_circular_relationship_validation(self, mock_decode):
        """Test circular relationship validation"""
        mock_decode.return_value = 1

        # First create a category
        response = client.post(
            "/categories/",
            json={"name": "ParentCatCirc"},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 201
        parent_id = response.json()["id"]

        # Try to set parent as its own parent
        response = client.put(
            f"/categories/{parent_id}",
            json={"name": "ParentCatCirc", "parent_id": parent_id},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 400
        assert "cannot be its own parent" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    def test_name_uniqueness_validation(self, mock_decode):
        """Test category name uniqueness validation"""
        mock_decode.return_value = 1

        # Create first category with a unique name
        unique_name = "UniqueCategoryXYZ123"
        response = client.post(
            "/categories/",
            json={"name": unique_name},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 201

        # Try to create another with same name
        response = client.post(
            "/categories/",
            json={"name": unique_name},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["error"]

    def test_internal_endpoint_security(self):
        """Test internal endpoint security improvements"""
        # Test without internal token
        response = client.get("/internal/categories/1?user_id=1")
        assert response.status_code == 403
        assert "Internal token required" in response.json()["error"]

        # Test with invalid internal token
        response = client.get(
            "/internal/categories/1?user_id=1",
            headers={"X-Internal-Token": "invalid_token"},
        )
        assert response.status_code == 403
        assert "Unauthorized internal access" in response.json()["error"]

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "category-service"

    @patch("app.dependencies.decode_token")
    def test_improved_error_messages(self, mock_decode):
        """Test improved error messages"""
        mock_decode.return_value = 1

        # Test category not found
        response = client.get(
            "/categories/999",
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 404
        assert "999" in response.json()["error"]

    def test_unauthorized_access(self):
        """Test unauthorized access handling"""
        # Test without authorization header
        response = client.get("/categories/")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["error"]

        # Test with invalid token format
        response = client.get(
            "/categories/",
            headers={"Authorization": "InvalidFormat token"},
        )
        assert response.status_code == 401
        assert "Invalid token format" in response.json()["error"]

    @patch("app.dependencies.decode_token")
    def test_hierarchical_category_retrieval(self, mock_decode):
        """Test hierarchical category retrieval"""
        mock_decode.return_value = 1

        # Create parent category with unique name to avoid conflicts
        response = client.post(
            "/categories/",
            json={"name": "ParentHierarchy123"},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 201
        parent_id = response.json()["id"]

        # Create child category
        response = client.post(
            "/categories/",
            json={"name": "ChildHierarchy123", "parent_id": parent_id},
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 201

        # Test hierarchical retrieval - response is now paginated
        response = client.get(
            "/categories/",
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        categories = data["items"]
        # Find the parent we just created
        parent_cat = next(
            (c for c in categories if c["name"] == "ParentHierarchy123"), None
        )
        assert parent_cat is not None
        assert len(parent_cat["children"]) == 1
        assert parent_cat["children"][0]["name"] == "ChildHierarchy123"

        # Test flat retrieval
        response = client.get(
            "/categories/?flat=true",
            headers={
                "Authorization": "Bearer valid_token",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        flat_names = [c["name"] for c in data["items"]]
        assert "ParentHierarchy123" in flat_names
        assert "ChildHierarchy123" in flat_names
