"""Tests for the analysis API router."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user_id, get_workspace_id
from app.schemas.analysis import AnalysisSection, AnalysisResponse
from app.exceptions import (
    FeatureNotAvailableError,
    CooldownActiveError,
    InsufficientDataError,
    LLMServiceError,
)


TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def override_user_id():
    return TEST_USER_ID


def override_workspace_id():
    return TEST_WORKSPACE_ID


app.dependency_overrides[get_current_user_id] = override_user_id
app.dependency_overrides[get_workspace_id] = override_workspace_id


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestGetPrompts:
    def test_returns_all_blocks(self, client):
        response = client.get("/api/v1/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_each_block_has_three_prompts(self, client):
        response = client.get("/api/v1/prompts")
        data = response.json()
        for block in data:
            assert len(block["prompts"]) == 3

    def test_block_structure(self, client):
        response = client.get("/api/v1/prompts")
        data = response.json()
        block = data[0]
        assert "block" in block
        assert "title_key" in block
        assert "prompts" in block
        prompt = block["prompts"][0]
        assert "id" in prompt
        assert "title_key" in prompt
        assert "description_key" in prompt
        assert "icon" in prompt


class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-assistant-service"


class TestAnalyzeEndpoint:
    def test_successful_analysis(self, client):
        result = AnalysisResponse(
            prompt_id="expenses_reduce_spending",
            sections=[
                AnalysisSection(title="Test", content="Content", priority="high"),
            ],
            cached=False,
            language="en",
        )

        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "expenses_reduce_spending", "language": "en"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_id"] == "expenses_reduce_spending"
        assert len(data["sections"]) == 1
        assert data["cached"] is False

    def test_invalid_prompt_id_returns_422(self, client):
        response = client.post(
            "/api/v1/analyze",
            json={"prompt_id": "nonexistent_prompt", "language": "en"},
        )
        assert response.status_code == 422

    def test_missing_prompt_id_returns_422(self, client):
        response = client.post(
            "/api/v1/analyze",
            json={"language": "en"},
        )
        assert response.status_code == 422

    def test_invalid_language_returns_422(self, client):
        response = client.post(
            "/api/v1/analyze",
            json={"prompt_id": "expenses_reduce_spending", "language": "fr"},
        )
        assert response.status_code == 422

    def test_feature_not_available_returns_402(self, client):
        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            side_effect=FeatureNotAvailableError(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "expenses_reduce_spending", "language": "en"},
            )

        assert response.status_code == 402
        data = response.json()
        assert data["errorCode"] == "FEATURE_NOT_AVAILABLE"

    def test_cooldown_active_returns_429(self, client):
        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            side_effect=CooldownActiveError(retry_after=3600),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "goals_realistic", "language": "ru"},
            )

        assert response.status_code == 429
        data = response.json()
        assert data["errorCode"] == "COOLDOWN_ACTIVE"
        assert data["retry_after"] == 3600

    def test_insufficient_data_returns_422(self, client):
        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            side_effect=InsufficientDataError("Not enough expenses"),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "expenses_anomalies", "language": "en"},
            )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "INSUFFICIENT_DATA"

    def test_llm_error_returns_503(self, client):
        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            side_effect=LLMServiceError(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "debts_pay_first", "language": "en"},
            )

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "LLM_SERVICE_ERROR"

    def test_default_language_is_ru(self, client):
        result = AnalysisResponse(
            prompt_id="expenses_save_more",
            sections=[],
            cached=False,
            language="ru",
        )

        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            return_value=result,
        ) as mock_run:
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "expenses_save_more"},
            )

        assert response.status_code == 200
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["language"] == "ru"

    def test_cached_response_marked(self, client):
        result = AnalysisResponse(
            prompt_id="goals_faster",
            sections=[AnalysisSection(title="Cached", content="From cache")],
            cached=True,
            language="en",
        )

        with patch(
            "app.routers.analysis.run_analysis",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"prompt_id": "goals_faster", "language": "en"},
            )

        assert response.status_code == 200
        assert response.json()["cached"] is True
