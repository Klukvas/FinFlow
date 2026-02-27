from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from uuid import UUID
from app.database import get_db
from app.dependencies import verify_internal_token
from app.services.goal import GoalService
from app.schemas.goal import GoalResponse
from app.models.goal import Goal, GoalStatus
from app.exceptions.goal_exceptions import GoalNotFoundError, GoalRetrievalError
from app.utils.logger import get_logger

logger = get_logger(__name__)
internal_router = APIRouter()


@internal_router.get("/goals/user/{user_id}", response_model=List[GoalResponse])
async def internal_get_user_goals(
    user_id: int,
    workspace_id: UUID = Query(..., description="Workspace ID for isolation"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint to get user goals"""
    service = GoalService(db)
    goals = service.get_goals(user_id, workspace_id, limit=200)
    return goals


@internal_router.get(
    "/goals/ai-summary",
    summary="Get goals summary for AI analysis",
    description="Internal endpoint returning aggregated goal data for AI assistant analysis",
    responses={
        200: {"description": "Goals summary retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_goals_ai_summary(
    user_id: Annotated[int, Query(description="User ID", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID")],
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
) -> dict:
    """
    Internal endpoint returning all active goals for AI analysis.

    Returns aggregated data without PII for the AI assistant to analyze
    goal progress and provide financial insights.
    """
    try:
        goals = (
            db.query(Goal)
            .filter(
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id,
                Goal.status == GoalStatus.ACTIVE,
            )
            .limit(200)
            .all()
        )
        return {
            "items": [
                {
                    "title": g.title,
                    "goal_type": str(g.goal_type.value) if g.goal_type else None,
                    "target_amount": float(g.target_amount),
                    "current_amount": float(g.current_amount) if g.current_amount else 0.0,
                    "progress_percentage": float(g.progress_percentage) if g.progress_percentage else 0.0,
                    "priority": str(g.priority.value) if g.priority else None,
                    "currency": g.currency,
                    "status": str(g.status.value) if g.status else None,
                }
                for g in goals
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching goals AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve goals summary",
        )


@internal_router.get("/goals/{goal_id}", response_model=GoalResponse)
async def internal_get_goal(
    goal_id: int,
    user_id: int = Query(..., description="User ID to validate ownership", gt=0),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint to get a specific goal"""
    service = GoalService(db)
    goal = service.get_goal(user_id, goal_id)
    return goal
