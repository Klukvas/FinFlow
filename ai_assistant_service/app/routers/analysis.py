from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.dependencies import get_current_user_id, get_workspace_id
from app.prompts.registry import PROMPT_BLOCKS
from app.schemas.analysis import AnalysisResponse, AnalysisSection
from app.schemas.prompts import AnalysisRequest, PromptBlockMetadata, PromptId
from app.services.analysis_orchestrator import run_analysis
from app.services import cache_service, rate_limiter
from app.services.subscription_client import check_feature_access

router = APIRouter(prefix="/api/v1", tags=["AI Assistant"])


@router.get(
    "/prompts",
    response_model=list[PromptBlockMetadata],
    summary="Get available prompt blocks",
    description="Returns metadata for all prompt blocks and cards for the frontend",
)
async def get_prompts(
    user_id: int = Depends(get_current_user_id),
) -> list[PromptBlockMetadata]:
    return PROMPT_BLOCKS


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Run AI analysis",
    description="Runs AI analysis for the selected prompt using user's financial data",
    responses={
        200: {"description": "Analysis completed successfully"},
        402: {"description": "Feature not available on current plan"},
        422: {"description": "Insufficient data for analysis"},
        429: {"description": "Rate limit / cooldown active"},
        503: {"description": "AI service unavailable"},
    },
)
async def analyze(
    request: AnalysisRequest,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
) -> AnalysisResponse:
    return await run_analysis(
        prompt_id=request.prompt_id,
        language=request.language,
        user_id=user_id,
        workspace_id=workspace_id,
    )


@router.get(
    "/results/{prompt_id}",
    response_model=AnalysisResponse | None,
    summary="Get last analysis result",
    description="Returns the most recent cached result for a prompt, or null if none exists",
)
async def get_last_result(
    prompt_id: PromptId,
    language: str = Query(default="ru"),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
) -> AnalysisResponse | None:
    cached = await cache_service.get_latest_result(
        str(workspace_id), prompt_id, language
    )
    if cached is None:
        return None
    sections = [AnalysisSection(**s) for s in cached["sections"]]
    return AnalysisResponse(
        prompt_id=prompt_id,
        sections=sections,
        cached=True,
        language=language,
    )


@router.get(
    "/usage",
    summary="Get AI usage info",
    description="Returns current month's usage and remaining quota",
)
async def get_usage(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
) -> dict:
    plan_code = await check_feature_access(user_id)
    if plan_code is None:
        return {"used": 0, "quota": 0, "remaining": 0, "resets_in": 0}
    return await rate_limiter.get_usage_info(user_id, str(workspace_id), plan_code)
