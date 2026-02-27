"""Tests for analysis orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.schemas.prompts import PromptId
from app.schemas.analysis import AnalysisSection, AnalysisResponse
from app.services.analysis_orchestrator import run_analysis
from app.exceptions import FeatureNotAvailableError, CooldownActiveError, InsufficientDataError


TEST_USER_ID = 42
TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_WORKSPACE_STR = str(TEST_WORKSPACE_ID)


def _make_sections(count: int = 2) -> list[AnalysisSection]:
    return [
        AnalysisSection(title=f"Section {i}", content=f"Content {i}", priority="medium")
        for i in range(count)
    ]


class TestRunAnalysisSuccess:
    async def test_full_pipeline_no_cache(self):
        """Test complete pipeline: subscription check -> rate limit -> set rate -> data -> LLM -> cache set."""
        sections = _make_sections(2)

        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="professional"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=None),
            patch("app.services.analysis_orchestrator.rate_limiter.set_rate_limit") as mock_rate_set,
            patch("app.services.analysis_orchestrator.aggregate_data", return_value=("formatted data", "abc123")),
            patch("app.services.analysis_orchestrator.cache_service.get_cached_result", return_value=None),
            patch("app.services.analysis_orchestrator.llm_service.analyze", return_value=sections),
            patch("app.services.analysis_orchestrator.cache_service.set_cached_result") as mock_cache_set,
        ):
            result = await run_analysis(
                PromptId.EXPENSES_REDUCE_SPENDING, "en", TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert isinstance(result, AnalysisResponse)
        assert result.prompt_id == "expenses_reduce_spending"
        assert len(result.sections) == 2
        assert result.cached is False
        assert result.language == "en"
        mock_cache_set.assert_called_once()
        mock_rate_set.assert_called_once_with(
            TEST_USER_ID, TEST_WORKSPACE_STR, "expenses_reduce_spending", "professional"
        )

    async def test_returns_cached_result(self):
        """Test that cached results are returned without calling LLM."""
        cached_data = {
            "sections": [
                {"title": "Cached", "content": "From cache", "priority": "high"},
            ]
        }

        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="enterprise"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=None),
            patch("app.services.analysis_orchestrator.rate_limiter.set_rate_limit"),
            patch("app.services.analysis_orchestrator.aggregate_data", return_value=("data", "hash1")),
            patch("app.services.analysis_orchestrator.cache_service.get_cached_result", return_value=cached_data),
            patch("app.services.analysis_orchestrator.llm_service.analyze") as mock_llm,
        ):
            result = await run_analysis(
                PromptId.GOALS_REALISTIC, "ru", TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert result.cached is True
        assert result.sections[0].title == "Cached"
        mock_llm.assert_not_called()


class TestRunAnalysisErrors:
    async def test_feature_not_available_raises_402(self):
        with patch("app.services.analysis_orchestrator.check_feature_access", return_value=None):
            with pytest.raises(FeatureNotAvailableError):
                await run_analysis(
                    PromptId.EXPENSES_REDUCE_SPENDING, "en", TEST_USER_ID, TEST_WORKSPACE_ID
                )

    async def test_rate_limited_raises_429(self):
        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="professional"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=3600),
        ):
            with pytest.raises(CooldownActiveError) as exc_info:
                await run_analysis(
                    PromptId.DEBTS_PAY_FIRST, "en", TEST_USER_ID, TEST_WORKSPACE_ID
                )
            assert exc_info.value.status_code == 429

    async def test_insufficient_data_propagates(self):
        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="professional"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=None),
            patch("app.services.analysis_orchestrator.rate_limiter.set_rate_limit"),
            patch(
                "app.services.analysis_orchestrator.aggregate_data",
                side_effect=InsufficientDataError("Not enough data"),
            ),
        ):
            with pytest.raises(InsufficientDataError):
                await run_analysis(
                    PromptId.EXPENSES_ANOMALIES, "en", TEST_USER_ID, TEST_WORKSPACE_ID
                )


class TestRunAnalysisPipeline:
    async def test_rate_limit_set_before_llm_call(self):
        """Verify that rate limit is set BEFORE LLM analysis (prevents double-spending)."""
        call_order = []

        async def mock_rate_set(*args, **kwargs):
            call_order.append("rate_set")

        async def mock_llm(*args, **kwargs):
            call_order.append("llm")
            return _make_sections()

        async def mock_cache_set(*args, **kwargs):
            call_order.append("cache_set")

        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="professional"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=None),
            patch("app.services.analysis_orchestrator.rate_limiter.set_rate_limit", side_effect=mock_rate_set),
            patch("app.services.analysis_orchestrator.aggregate_data", return_value=("data", "hash")),
            patch("app.services.analysis_orchestrator.cache_service.get_cached_result", return_value=None),
            patch("app.services.analysis_orchestrator.llm_service.analyze", side_effect=mock_llm),
            patch("app.services.analysis_orchestrator.cache_service.set_cached_result", side_effect=mock_cache_set),
        ):
            await run_analysis(PromptId.EXPENSES_SAVE_MORE, "en", TEST_USER_ID, TEST_WORKSPACE_ID)

        assert call_order == ["rate_set", "llm", "cache_set"]

    async def test_enterprise_plan_passed_to_rate_limiter(self):
        with (
            patch("app.services.analysis_orchestrator.check_feature_access", return_value="enterprise"),
            patch("app.services.analysis_orchestrator.rate_limiter.check_rate_limit", return_value=None) as mock_check,
            patch("app.services.analysis_orchestrator.rate_limiter.set_rate_limit") as mock_set,
            patch("app.services.analysis_orchestrator.aggregate_data", return_value=("data", "hash")),
            patch("app.services.analysis_orchestrator.cache_service.get_cached_result", return_value=None),
            patch("app.services.analysis_orchestrator.llm_service.analyze", return_value=_make_sections()),
            patch("app.services.analysis_orchestrator.cache_service.set_cached_result"),
        ):
            await run_analysis(PromptId.DEBTS_RISK_ASSESSMENT, "ru", TEST_USER_ID, TEST_WORKSPACE_ID)

        mock_check.assert_called_once_with(
            TEST_USER_ID, TEST_WORKSPACE_STR, "debts_risk_assessment", "enterprise"
        )
        mock_set.assert_called_once_with(
            TEST_USER_ID, TEST_WORKSPACE_STR, "debts_risk_assessment", "enterprise"
        )
