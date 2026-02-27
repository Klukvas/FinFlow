"""Tests for LLM service (Anthropic integration)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic

from app.schemas.prompts import PromptId
from app.schemas.analysis import AnalysisSection
from app.services import llm_service
from app.exceptions import LLMServiceError, LLMRateLimitError


class TestBuildUserPrompt:
    def test_builds_prompt_with_data(self):
        result = llm_service._build_user_prompt(
            PromptId.EXPENSES_REDUCE_SPENDING, "en", "some data"
        )
        assert "some data" in result
        assert "{data}" not in result

    def test_falls_back_to_english(self):
        result = llm_service._build_user_prompt(
            PromptId.EXPENSES_REDUCE_SPENDING, "fr", "test data"
        )
        # Should fall back to English when French is not available
        assert "test data" in result

    def test_russian_template(self):
        result = llm_service._build_user_prompt(
            PromptId.EXPENSES_REDUCE_SPENDING, "ru", "данные"
        )
        assert "данные" in result


class TestParseSections:
    def test_valid_json_array(self):
        raw = json.dumps([
            {"title": "Section 1", "content": "Content 1", "priority": "high"},
            {"title": "Section 2", "content": "Content 2", "priority": "low"},
        ])
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 2
        assert sections[0].title == "Section 1"
        assert sections[0].priority == "high"
        assert sections[1].title == "Section 2"

    def test_json_with_surrounding_text(self):
        raw = 'Here is the analysis:\n[{"title": "T", "content": "C", "priority": "medium"}]\nDone.'
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1
        assert sections[0].title == "T"

    def test_invalid_json_falls_back(self):
        raw = "This is just plain text analysis without JSON."
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1
        assert sections[0].title == "Analysis"
        assert "plain text analysis" in sections[0].content

    def test_empty_content_items_filtered(self):
        raw = json.dumps([
            {"title": "Good", "content": "Has content", "priority": "high"},
            {"title": "Empty", "content": "", "priority": "low"},
        ])
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1
        assert sections[0].title == "Good"

    def test_missing_title_uses_default(self):
        raw = json.dumps([{"content": "Some content"}])
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1
        assert sections[0].title == "Analysis"

    def test_missing_priority_uses_medium(self):
        raw = json.dumps([{"title": "Test", "content": "Content"}])
        sections = llm_service._parse_sections(raw)
        assert sections[0].priority == "medium"

    def test_non_dict_items_in_array_skipped(self):
        raw = json.dumps([
            {"title": "Valid", "content": "Content"},
            "not a dict",
            42,
        ])
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1

    def test_json_object_instead_of_array_falls_back(self):
        raw = json.dumps({"title": "Single", "content": "Not an array"})
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1
        assert sections[0].title == "Analysis"

    def test_whitespace_handling(self):
        raw = '   \n  [{"title": "T", "content": "C"}]  \n  '
        sections = llm_service._parse_sections(raw)
        assert len(sections) == 1


class TestAnalyze:
    async def test_successful_analysis(self, mock_anthropic_response, sample_analysis_sections_json):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=mock_anthropic_response(sample_analysis_sections_json)
        )

        with patch.object(llm_service, "_get_client", return_value=mock_client):
            sections = await llm_service.analyze(
                PromptId.EXPENSES_REDUCE_SPENDING, "en", "expense data here"
            )

        assert len(sections) == 2
        assert sections[0].title == "Spending Analysis"
        assert sections[0].priority == "high"
        mock_client.messages.create.assert_called_once()

    async def test_rate_limit_raises_llm_rate_limit_error(self):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body={"error": {"message": "Rate limited"}},
            )
        )

        with patch.object(llm_service, "_get_client", return_value=mock_client):
            with pytest.raises(LLMRateLimitError):
                await llm_service.analyze(
                    PromptId.EXPENSES_REDUCE_SPENDING, "en", "data"
                )

    async def test_api_error_raises_llm_service_error(self):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIError(
                message="Server error",
                request=MagicMock(),
                body={"error": {"message": "Server error"}},
            )
        )

        with patch.object(llm_service, "_get_client", return_value=mock_client):
            with pytest.raises(LLMServiceError):
                await llm_service.analyze(
                    PromptId.GOALS_REALISTIC, "ru", "data"
                )

    async def test_unexpected_error_raises_llm_service_error(self):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )

        with patch.object(llm_service, "_get_client", return_value=mock_client):
            with pytest.raises(LLMServiceError):
                await llm_service.analyze(
                    PromptId.DEBTS_PAY_FIRST, "en", "data"
                )

    async def test_model_and_tokens_passed_correctly(self, mock_anthropic_response):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=mock_anthropic_response('[{"title":"T","content":"C"}]')
        )

        with patch.object(llm_service, "_get_client", return_value=mock_client):
            await llm_service.analyze(
                PromptId.EXPENSES_ANOMALIES, "uk", "data"
            )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == llm_service.settings.ANTHROPIC_MODEL
        assert call_kwargs["max_tokens"] == llm_service.settings.ANTHROPIC_MAX_TOKENS
        assert call_kwargs["messages"][0]["role"] == "user"


class TestGetClient:
    def test_singleton_pattern(self):
        llm_service._client = None
        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            client1 = llm_service._get_client()
            client2 = llm_service._get_client()

            assert client1 is client2
            mock_cls.assert_called_once()

        # Cleanup
        llm_service._client = None
