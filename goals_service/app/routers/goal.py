from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.goal import GoalService
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalResponse, GoalListResponse, GoalStatistics,
    GoalProgressUpdate, MilestoneCreate, MilestoneResponse, MilestoneProgressUpdate
)
from app.models.goal import GoalStatus, GoalType, GoalPriority
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, MilestoneNotFoundError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new financial goal"""
    try:
        service = GoalService(db)
        goal = service.create_goal(user_id, goal_data)
        return goal
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/", response_model=GoalListResponse)
async def get_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[GoalStatus] = Query(None),
    goal_type: Optional[GoalType] = Query(None),
    priority: Optional[GoalPriority] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's financial goals with optional filtering"""
    try:
        service = GoalService(db)
        goals = service.get_goals(user_id, skip, limit, status, goal_type, priority)
        
        # Get total count for pagination
        total = len(goals)
        pages = (total + limit - 1) // limit
        
        return GoalListResponse(
            items=goals,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific financial goal"""
    try:
        service = GoalService(db)
        goal = service.get_goal(user_id, goal_id)
        return goal
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a financial goal"""
    try:
        service = GoalService(db)
        goal = service.update_goal(user_id, goal_id, goal_data)
        return goal
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{goal_id}/progress", response_model=GoalResponse)
async def update_goal_progress(
    goal_id: int,
    progress_data: GoalProgressUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update goal progress"""
    try:
        service = GoalService(db)
        goal = service.update_goal_progress(user_id, goal_id, progress_data)
        return goal
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a financial goal"""
    try:
        service = GoalService(db)
        service.delete_goal(user_id, goal_id)
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/statistics/overview", response_model=GoalStatistics)
async def get_goal_statistics(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get goal statistics for the user"""
    try:
        service = GoalService(db)
        stats = service.get_goal_statistics(user_id)
        return stats
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# Milestone endpoints
@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    goal_id: int,
    milestone_data: MilestoneCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a milestone for a goal"""
    try:
        service = GoalService(db)
        milestone = service.create_milestone(user_id, goal_id, milestone_data)
        return milestone
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{goal_id}/milestones", response_model=List[MilestoneResponse])
async def get_milestones(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get milestones for a goal"""
    try:
        service = GoalService(db)
        milestones = service.get_milestones(user_id, goal_id)
        return milestones
    except GoalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{goal_id}/milestones/{milestone_id}/progress", response_model=MilestoneResponse)
async def update_milestone_progress(
    goal_id: int,
    milestone_id: int,
    progress_data: MilestoneProgressUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update milestone progress"""
    try:
        service = GoalService(db)
        milestone = service.update_milestone_progress(user_id, goal_id, milestone_id, progress_data)
        return milestone
    except (GoalNotFoundError, MilestoneNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GoalValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
