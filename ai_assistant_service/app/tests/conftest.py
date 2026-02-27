import os

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-for-testing-only")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-secret-token")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("EXPENSE_SERVICE_URL", "http://localhost:8003")
os.environ.setdefault("INCOME_SERVICE_URL", "http://localhost:8004")
os.environ.setdefault("DEBT_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("GOALS_SERVICE_URL", "http://localhost:8006")
os.environ.setdefault("ACCOUNT_SERVICE_URL", "http://localhost:8009")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("RECURRING_SERVICE_URL", "http://localhost:8010")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from httpx import Response


TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def mock_redis():
    """Mock Redis client for cache and rate limiter tests."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.ttl = AsyncMock(return_value=-2)
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture(autouse=True)
def reset_redis_client():
    """Reset global Redis client singleton between tests."""
    from app.services import cache_service
    cache_service._redis_client = None
    yield
    cache_service._redis_client = None


@pytest.fixture
def mock_anthropic_response():
    """Create a mock Anthropic API response."""
    def _make(text: str, input_tokens: int = 100, output_tokens: int = 200):
        response = MagicMock()
        content_block = MagicMock()
        content_block.text = text
        response.content = [content_block]
        response.usage = MagicMock()
        response.usage.input_tokens = input_tokens
        response.usage.output_tokens = output_tokens
        return response
    return _make


@pytest.fixture
def sample_analysis_sections_json():
    """Valid JSON response from LLM."""
    return '''[
        {"title": "Spending Analysis", "content": "Your top category is **Food** at $500/month.", "priority": "high"},
        {"title": "Recommendations", "content": "Consider reducing dining out.", "priority": "medium"}
    ]'''


@pytest.fixture
def sample_expense_data():
    """Sample expense data from internal service."""
    return {
        "items": [
            {"amount": 100.0, "category_id": 1, "currency": "USD", "date": "2026-01-15", "description": "Groceries"},
            {"amount": 50.0, "category_id": 2, "currency": "USD", "date": "2026-01-16", "description": "Transport"},
            {"amount": 200.0, "category_id": 1, "currency": "USD", "date": "2026-01-20", "description": "Groceries"},
            {"amount": 75.0, "category_id": 3, "currency": "USD", "date": "2026-01-22", "description": "Utilities"},
            {"amount": 300.0, "category_id": 4, "currency": "USD", "date": "2026-01-25", "description": "Rent"},
        ]
    }


@pytest.fixture
def sample_income_data():
    """Sample income data from internal service."""
    return {
        "items": [
            {"amount": 5000.0, "category_id": 10, "currency": "USD", "date": "2026-01-01"},
        ]
    }


@pytest.fixture
def sample_category_data():
    """Sample category data from internal service."""
    return {
        "items": [
            {"id": 1, "name": "Food", "type": "expense", "parent_id": None},
            {"id": 2, "name": "Transport", "type": "expense", "parent_id": None},
            {"id": 3, "name": "Utilities", "type": "expense", "parent_id": None},
            {"id": 4, "name": "Rent", "type": "expense", "parent_id": None},
            {"id": 10, "name": "Salary", "type": "income", "parent_id": None},
        ]
    }


@pytest.fixture
def sample_debt_data():
    """Sample debt data from internal service."""
    return {
        "items": [
            {"name": "Credit Card", "type": "credit", "balance": 5000.0, "interest_rate": 19.9, "due_date": "2027-01-01"},
        ]
    }


@pytest.fixture
def sample_goal_data():
    """Sample goal data from internal service."""
    return {
        "items": [
            {"title": "Emergency Fund", "type": "savings", "target": 10000.0, "current": 3000.0, "progress_pct": 30, "priority": "high"},
        ]
    }


@pytest.fixture
def mock_httpx_response():
    """Factory for creating mock httpx responses."""
    def _make(status_code: int = 200, json_body: dict | None = None):
        response = MagicMock(spec=Response)
        response.status_code = status_code
        if json_body is not None:
            response.json.return_value = json_body
        return response
    return _make
