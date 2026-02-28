"""E2E tests for ai_assistant_service (port 8015).

All tests work WITHOUT a real Anthropic key — the LLM call only happens
deep in the /analyze pipeline after subscription check and data validation.
"""
from __future__ import annotations

import pytest

from tests.e2e.clients.ai_assistant_client import AiAssistantApiClient

pytestmark = pytest.mark.ai_assistant


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:

    async def test_health_returns_200(self):
        client = AiAssistantApiClient()
        ok = await client.health_check()
        assert ok, "ai_assistant_service /health should return 200"


# ---------------------------------------------------------------------------
# 2. Unauthenticated access → 401
# ---------------------------------------------------------------------------

class TestUnauthenticated:

    async def test_prompts_requires_auth(self):
        client = AiAssistantApiClient()
        result = await client.get_prompts()
        assert result.status_code == 401 or result.status_code == 403

    async def test_analyze_requires_auth(self):
        client = AiAssistantApiClient()
        result = await client.analyze("expenses_reduce_spending")
        assert result.status_code == 401 or result.status_code == 403

    async def test_results_requires_auth(self):
        client = AiAssistantApiClient()
        result = await client.get_result("expenses_reduce_spending")
        assert result.status_code == 401 or result.status_code == 403

    async def test_usage_requires_auth(self):
        client = AiAssistantApiClient()
        result = await client.get_usage()
        assert result.status_code == 401 or result.status_code == 403


# ---------------------------------------------------------------------------
# 3. Prompts listing (authenticated, basic plan is enough)
# ---------------------------------------------------------------------------

class TestPromptsListing:

    async def test_returns_three_blocks(self, ai_assistant_client):
        result = await ai_assistant_client.get_prompts()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) == 3, f"Expected 3 prompt blocks, got {len(data)}"

    async def test_nine_prompts_total(self, ai_assistant_client):
        result = await ai_assistant_client.get_prompts()
        data = result.raise_on_error()
        total = sum(len(block["prompts"]) for block in data)
        assert total == 9, f"Expected 9 prompts total, got {total}"

    async def test_prompt_metadata_structure(self, ai_assistant_client):
        result = await ai_assistant_client.get_prompts()
        data = result.raise_on_error()
        first_prompt = data[0]["prompts"][0]
        assert "id" in first_prompt
        assert "block" in first_prompt
        assert "title_key" in first_prompt
        assert "description_key" in first_prompt
        assert "icon" in first_prompt


# ---------------------------------------------------------------------------
# 4. Subscription gating (basic plan → blocked)
# ---------------------------------------------------------------------------

class TestSubscriptionGating:

    async def test_analyze_blocked_for_basic_plan(self, ai_assistant_client):
        """Basic-plan user should get 402 FEATURE_NOT_AVAILABLE."""
        result = await ai_assistant_client.analyze("expenses_reduce_spending")
        assert result.status_code == 402, f"Expected 402, got {result.status_code}: {result.error}"
        assert result.raw.get("errorCode") == "FEATURE_NOT_AVAILABLE", f"raw={result.raw}"

    async def test_usage_returns_zero_quota_for_basic(self, ai_assistant_client):
        """Basic-plan user should see quota=0."""
        result = await ai_assistant_client.get_usage()
        data = result.raise_on_error()
        assert data["quota"] == 0
        assert data["remaining"] == 0


# ---------------------------------------------------------------------------
# 5. Insufficient data (professional plan, but no financial data)
# ---------------------------------------------------------------------------

class TestInsufficientData:

    async def test_expenses_prompt_needs_data(self, pro_ai_client):
        """No expenses → 422 INSUFFICIENT_DATA."""
        result = await pro_ai_client.analyze("expenses_reduce_spending")
        assert result.status_code == 422, f"Expected 422, got {result.status_code}: {result.error}"
        assert result.raw.get("errorCode") == "INSUFFICIENT_DATA", f"raw={result.raw}"

    async def test_goals_prompt_needs_data(self, pro_ai_client):
        """No goals → 422 INSUFFICIENT_DATA."""
        result = await pro_ai_client.analyze("goals_realistic")
        assert result.status_code == 422, f"Expected 422, got {result.status_code}: {result.error}"
        assert result.raw.get("errorCode") == "INSUFFICIENT_DATA", f"raw={result.raw}"

    async def test_debts_prompt_needs_data(self, pro_ai_client):
        """No debts → 422 INSUFFICIENT_DATA."""
        result = await pro_ai_client.analyze("debts_pay_first")
        assert result.status_code == 422, f"Expected 422, got {result.status_code}: {result.error}"
        assert result.raw.get("errorCode") == "INSUFFICIENT_DATA", f"raw={result.raw}"


# ---------------------------------------------------------------------------
# 6. Cached results (empty cache)
# ---------------------------------------------------------------------------

class TestCachedResults:

    async def test_no_cached_result_returns_null(self, pro_ai_client):
        """Fresh user has no cached results → null body."""
        result = await pro_ai_client.get_result("expenses_reduce_spending")
        assert result.status_code == 200, f"Expected 200, got {result.status_code}: {result.error}"
        assert result.data is None, f"Expected null body but got: {result.data}"


# ---------------------------------------------------------------------------
# 7. Usage stats (professional plan)
# ---------------------------------------------------------------------------

class TestUsageStats:

    async def test_professional_quota_is_five(self, pro_ai_client):
        result = await pro_ai_client.get_usage()
        data = result.raise_on_error()
        assert data["quota"] == 5

    async def test_fresh_user_has_zero_used(self, pro_ai_client):
        result = await pro_ai_client.get_usage()
        data = result.raise_on_error()
        assert data["used"] == 0


# ---------------------------------------------------------------------------
# 8. Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:

    async def test_invalid_prompt_id(self, pro_ai_client):
        """Unknown prompt_id → 422."""
        result = await pro_ai_client.analyze("nonexistent_prompt")
        assert result.status_code == 422

    async def test_invalid_language(self, pro_ai_client):
        """Invalid language code → 422."""
        result = await pro_ai_client.analyze("expenses_reduce_spending", language="xx")
        assert result.status_code == 422

    async def test_invalid_prompt_id_in_results(self, pro_ai_client):
        """Unknown prompt_id in results endpoint → 422."""
        result = await pro_ai_client.get_result("nonexistent_prompt")
        assert result.status_code == 422
