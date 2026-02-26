from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from app.models.goal import GoalType, GoalStatus, GoalPriority


class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    goal_type: GoalType
    priority: GoalPriority = GoalPriority.MEDIUM
    target_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    target_date: Optional[datetime] = None
    is_milestone_based: bool = False

    @field_validator('target_date', mode='before')
    @classmethod
    def parse_target_date(cls, v):
        """Accept both date and datetime formats"""
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        if isinstance(v, str):
            # Try date-only format first (YYYY-MM-DD)
            if len(v) == 10 and '-' in v:
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            # Try datetime format
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return v  # Let Pydantic handle validation error

    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('Target amount must be greater than 0')
        return round(v, 2)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    goal_type: Optional[GoalType] = None
    priority: Optional[GoalPriority] = None
    target_amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None
    is_milestone_based: Optional[bool] = None

    @field_validator('target_date', mode='before')
    @classmethod
    def parse_target_date(cls, v):
        """Accept both date and datetime formats"""
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        if isinstance(v, str):
            if len(v) == 10 and '-' in v:
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return v

    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Target amount must be greater than 0')
        return round(v, 2) if v is not None else v


class GoalProgressUpdate(BaseModel):
    current_amount: float = Field(..., ge=0)

    @validator('current_amount')
    def validate_current_amount(cls, v):
        return round(v, 2)


class GoalResponse(GoalBase):
    id: int
    user_id: int
    workspace_id: UUID
    current_amount: float
    progress_percentage: float
    status: GoalStatus
    start_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_read_only: bool = False

    class Config:
        from_attributes = True


class GoalWithMilestones(GoalResponse):
    milestones: List['MilestoneResponse'] = []


class GoalListResponse(BaseModel):
    items: List[GoalResponse]
    total: int
    page: int
    size: int
    pages: int


class GoalStatistics(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    total_target_amount: float
    total_current_amount: float
    overall_progress: float
    currency: str
    goals_by_type: dict
    goals_by_priority: dict


# Milestone schemas
class MilestoneBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    target_amount: float = Field(..., gt=0)
    order_index: int = 0

    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('Target amount must be greater than 0')
        return round(v, 2)


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    target_amount: Optional[float] = Field(None, gt=0)
    order_index: Optional[int] = None

    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Target amount must be greater than 0')
        return round(v, 2) if v is not None else v


class MilestoneProgressUpdate(BaseModel):
    current_amount: float = Field(..., ge=0)

    @validator('current_amount')
    def validate_current_amount(cls, v):
        return round(v, 2)


class MilestoneResponse(MilestoneBase):
    id: int
    goal_id: int
    current_amount: float
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Update forward references
GoalWithMilestones.model_rebuild()
