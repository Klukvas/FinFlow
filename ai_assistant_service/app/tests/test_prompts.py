"""Tests for prompt registry, templates, and schemas."""

import pytest

from app.schemas.prompts import PromptId, PromptBlock, AnalysisRequest, PromptBlockMetadata
from app.schemas.analysis import AnalysisSection, AnalysisResponse
from app.prompts.registry import PROMPT_DATA_SOURCES, PROMPT_MIN_THRESHOLDS, PROMPT_BLOCKS
from app.prompts.templates import SYSTEM_PROMPT, PROMPT_TEMPLATES


class TestPromptId:
    def test_all_prompt_ids_exist(self):
        assert len(PromptId) == 9

    def test_prompt_id_values(self):
        assert PromptId.EXPENSES_REDUCE_SPENDING.value == "expenses_reduce_spending"
        assert PromptId.GOALS_REALISTIC.value == "goals_realistic"
        assert PromptId.DEBTS_PAY_FIRST.value == "debts_pay_first"

    def test_prompt_block_values(self):
        assert PromptBlock.EXPENSES.value == "expenses"
        assert PromptBlock.GOALS.value == "goals"
        assert PromptBlock.DEBTS.value == "debts"


class TestAnalysisRequest:
    def test_valid_request(self):
        req = AnalysisRequest(prompt_id=PromptId.EXPENSES_REDUCE_SPENDING, language="en")
        assert req.prompt_id == PromptId.EXPENSES_REDUCE_SPENDING
        assert req.language == "en"

    def test_default_language(self):
        req = AnalysisRequest(prompt_id=PromptId.GOALS_REALISTIC)
        assert req.language == "ru"

    def test_invalid_prompt_id_rejected(self):
        with pytest.raises(Exception):
            AnalysisRequest(prompt_id="nonexistent_prompt")


class TestAnalysisSection:
    def test_valid_section(self):
        section = AnalysisSection(
            title="Test", content="Some **markdown** content", priority="high"
        )
        assert section.title == "Test"
        assert section.priority == "high"

    def test_default_priority(self):
        section = AnalysisSection(title="Test", content="Content")
        assert section.priority == "medium"


class TestAnalysisResponse:
    def test_valid_response(self):
        resp = AnalysisResponse(
            prompt_id="expenses_reduce_spending",
            sections=[AnalysisSection(title="T", content="C")],
            cached=False,
            language="ru",
        )
        assert resp.prompt_id == "expenses_reduce_spending"
        assert len(resp.sections) == 1
        assert resp.cached is False

    def test_defaults(self):
        resp = AnalysisResponse(
            prompt_id="test",
            sections=[],
        )
        assert resp.cached is False
        assert resp.language == "ru"


class TestPromptDataSources:
    def test_all_prompts_have_data_sources(self):
        for prompt_id in PromptId:
            assert prompt_id in PROMPT_DATA_SOURCES, f"Missing data sources for {prompt_id}"
            assert len(PROMPT_DATA_SOURCES[prompt_id]) > 0

    def test_data_source_names_are_valid(self):
        valid_sources = {"expenses", "incomes", "debts", "goals", "accounts", "categories", "recurring"}
        for prompt_id, sources in PROMPT_DATA_SOURCES.items():
            for source in sources:
                assert source in valid_sources, f"Invalid source '{source}' for {prompt_id}"

    def test_expenses_prompts_need_expenses(self):
        for pid in [PromptId.EXPENSES_REDUCE_SPENDING, PromptId.EXPENSES_SAVE_MORE, PromptId.EXPENSES_ANOMALIES]:
            assert "expenses" in PROMPT_DATA_SOURCES[pid]

    def test_debts_prompts_need_debts(self):
        for pid in [PromptId.DEBTS_PAY_FIRST, PromptId.DEBTS_RISK_ASSESSMENT, PromptId.DEBTS_REPAYMENT_STRATEGY]:
            assert "debts" in PROMPT_DATA_SOURCES[pid]

    def test_goals_prompts_need_goals(self):
        for pid in [PromptId.GOALS_REALISTIC, PromptId.GOALS_FASTER, PromptId.GOALS_PRIORITIZE]:
            assert "goals" in PROMPT_DATA_SOURCES[pid]


class TestPromptMinThresholds:
    def test_all_prompts_have_thresholds(self):
        for prompt_id in PromptId:
            assert prompt_id in PROMPT_MIN_THRESHOLDS, f"Missing threshold for {prompt_id}"

    def test_thresholds_are_positive(self):
        for prompt_id, thresholds in PROMPT_MIN_THRESHOLDS.items():
            for source, min_count in thresholds.items():
                assert min_count > 0, f"Threshold must be > 0 for {prompt_id}/{source}"

    def test_anomalies_needs_more_data(self):
        assert PROMPT_MIN_THRESHOLDS[PromptId.EXPENSES_ANOMALIES]["expenses"] == 10


class TestPromptBlocks:
    def test_three_blocks(self):
        assert len(PROMPT_BLOCKS) == 3

    def test_each_block_has_three_prompts(self):
        for block in PROMPT_BLOCKS:
            assert len(block.prompts) == 3

    def test_block_types(self):
        blocks = [b.block for b in PROMPT_BLOCKS]
        assert PromptBlock.EXPENSES in blocks
        assert PromptBlock.GOALS in blocks
        assert PromptBlock.DEBTS in blocks

    def test_all_prompts_have_icon(self):
        for block in PROMPT_BLOCKS:
            for prompt in block.prompts:
                assert prompt.icon, f"Missing icon for {prompt.id}"

    def test_all_prompts_have_i18n_keys(self):
        for block in PROMPT_BLOCKS:
            assert block.title_key.startswith("aiAssistant.blocks.")
            for prompt in block.prompts:
                assert prompt.title_key.startswith("aiAssistant.prompts.")
                assert prompt.description_key.startswith("aiAssistant.prompts.")

    def test_serialization(self):
        """PromptBlockMetadata should serialize correctly for API response."""
        block = PROMPT_BLOCKS[0]
        data = block.model_dump()
        assert "block" in data
        assert "title_key" in data
        assert "prompts" in data
        assert len(data["prompts"]) == 3


class TestPromptTemplates:
    def test_system_prompt_has_language_placeholder(self):
        assert "{language}" in SYSTEM_PROMPT

    def test_system_prompt_formats_correctly(self):
        formatted = SYSTEM_PROMPT.format(language="en")
        assert "en" in formatted
        assert "{language}" not in formatted

    def test_all_prompts_have_templates(self):
        for prompt_id in PromptId:
            assert prompt_id in PROMPT_TEMPLATES, f"Missing template for {prompt_id}"

    def test_all_templates_have_three_languages(self):
        for prompt_id, templates in PROMPT_TEMPLATES.items():
            assert "ru" in templates, f"Missing ru template for {prompt_id}"
            assert "en" in templates, f"Missing en template for {prompt_id}"
            assert "uk" in templates, f"Missing uk template for {prompt_id}"

    def test_all_templates_have_data_placeholder(self):
        for prompt_id, templates in PROMPT_TEMPLATES.items():
            for lang, template in templates.items():
                assert "{data}" in template, f"Missing {{data}} placeholder in {prompt_id}/{lang}"

    def test_template_format_works(self):
        template = PROMPT_TEMPLATES[PromptId.EXPENSES_REDUCE_SPENDING]["en"]
        formatted = template.format(data="some financial data here")
        assert "some financial data here" in formatted
        assert "{data}" not in formatted
