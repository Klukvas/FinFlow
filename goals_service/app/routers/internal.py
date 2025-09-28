from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import verify_internal_token
from app.services.goal import GoalService
from app.schemas.goal import GoalResponse
from app.exceptions.goal_exceptions import GoalNotFoundError, GoalValidationError
from app.utils.logger import get_logger

logger = get_logger(__name__)
internal_router = APIRouter()


@internal_router.get("/goals/user/{user_id}", response_model=List[GoalResponse])
async def internal_get_user_goals(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint to get user goals"""
    try:
        service = GoalService(db)
        goals = service.get_goals(user_id, limit=1000)  # Get all goals
        return goals
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@internal_router.get("/goals/{goal_id}", response_model=GoalResponse)
async def internal_get_goal(
    goal_id: int,
    user_id: int = Query(..., description="User ID to validate ownership", gt=0),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Internal endpoint to get a specific goal"""
    try:
        service = GoalService(db)
        goal = service.get_goal(user_id, goal_id)
        return goal
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
