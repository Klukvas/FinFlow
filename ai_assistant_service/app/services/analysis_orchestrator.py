import logging
from uuid import UUID

from app.exceptions import QuotaExhaustedError, FeatureNotAvailableError, InsufficientDataError, LLMServiceError, LLMRateLimitError
from app.schemas.analysis import AnalysisResponse, AnalysisSection
from app.schemas.prompts import PromptId
from app.services import cache_service, rate_limiter, llm_service
from app.services.data_aggregator import aggregate_data
from app.services.subscription_client import check_feature_access

logger = logging.getLogger(__name__)


async def run_analysis(
    prompt_id: PromptId,
    language: str,
    user_id: int,
    workspace_id: UUID,
) -> AnalysisResponse:
    """Full analysis pipeline: access check -> quota -> data -> cache -> LLM -> store."""

    # 1. Check subscription feature access
    plan_code, quota = await check_feature_access(user_id)
    if plan_code is None:
        raise FeatureNotAvailableError()

    # 2. Check monthly quota (global, not per-prompt)
    if quota is not None:  # None = unlimited
        retry_after = await rate_limiter.check_rate_limit(
            user_id, str(workspace_id), quota
        )
        if retry_after is not None:
            raise QuotaExhaustedError(retry_after=retry_after)

    # 3. Increment usage immediately to prevent concurrent double-spending
    await rate_limiter.increment_usage(user_id, str(workspace_id))

    # 4. Aggregate financial data (refund usage if insufficient data)
    try:
        formatted_data, data_hash = await aggregate_data(prompt_id, user_id, workspace_id)
    except InsufficientDataError:
        await rate_limiter.decrement_usage(user_id, str(workspace_id))
        raise

    # 5. Check cache
    cached = await cache_service.get_cached_result(
        str(workspace_id), prompt_id.value, language, data_hash
    )
    if cached is not None:
        # Refund usage for cache hits — no LLM cost
        await rate_limiter.decrement_usage(user_id, str(workspace_id))
        logger.info(f"Returning cached result for prompt={prompt_id.value}")
        sections = [AnalysisSection(**s) for s in cached["sections"]]
        return AnalysisResponse(
            prompt_id=prompt_id.value,
            sections=sections,
            cached=True,
            language=language,
        )

    # 6. Call LLM (refund usage on failure)
    try:
        sections = await llm_service.analyze(prompt_id, language, formatted_data)
    except (LLMServiceError, LLMRateLimitError):
        await rate_limiter.decrement_usage(user_id, str(workspace_id))
        raise

    # 7. Store in cache (both hash-based and latest)
    result_dict = {
        "sections": [s.model_dump() for s in sections],
    }
    await cache_service.set_cached_result(
        str(workspace_id), prompt_id.value, language, data_hash, result_dict
    )
    await cache_service.set_latest_result(
        str(workspace_id), prompt_id.value, language, result_dict
    )

    logger.info(f"Analysis complete for prompt={prompt_id.value}, user={user_id}")
    return AnalysisResponse(
        prompt_id=prompt_id.value,
        sections=sections,
        cached=False,
        language=language,
    )
