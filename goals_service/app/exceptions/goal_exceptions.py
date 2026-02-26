from fastapi import HTTPException
from typing import Any, Dict, Optional


class GoalServiceError(HTTPException):
    """Base exception for goal service errors"""
    def __init__(self, detail: str, status_code: int = 400, error_code: str = "GOAL_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class GoalNotFoundError(GoalServiceError):
    """Raised when a goal is not found"""
    def __init__(self, detail: str = "Goal not found"):
        super().__init__(detail=detail, status_code=404, error_code="GOAL_NOT_FOUND")


class GoalValidationError(GoalServiceError):
    """Raised when goal validation fails"""
    def __init__(self, detail: str = "Goal validation failed"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_VALIDATION_FAILED")


class GoalOwnershipError(GoalServiceError):
    """Raised when user doesn't own the goal"""
    def __init__(self, detail: str = "Access denied to goal"):
        super().__init__(detail=detail, status_code=403, error_code="GOAL_ACCESS_DENIED")


class MilestoneNotFoundError(GoalServiceError):
    """Raised when a milestone is not found"""
    def __init__(self, detail: str = "Milestone not found"):
        super().__init__(detail=detail, status_code=404, error_code="MILESTONE_NOT_FOUND")


class MilestoneValidationError(GoalServiceError):
    """Raised when milestone validation fails"""
    def __init__(self, detail: str = "Milestone validation failed"):
        super().__init__(detail=detail, status_code=422, error_code="MILESTONE_VALIDATION_FAILED")


class GoalProgressError(GoalServiceError):
    """Raised when goal progress update fails"""
    def __init__(self, detail: str = "Failed to update goal progress"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_PROGRESS_UPDATE_FAILED")


class GoalCreationError(GoalServiceError):
    """Raised when goal creation fails"""
    def __init__(self, detail: str = "Failed to create goal"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_CREATION_FAILED")


class GoalUpdateError(GoalServiceError):
    """Raised when goal update fails"""
    def __init__(self, detail: str = "Failed to update goal"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_UPDATE_FAILED")


class GoalDeletionError(GoalServiceError):
    """Raised when goal deletion fails"""
    def __init__(self, detail: str = "Failed to delete goal"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_DELETION_FAILED")


class GoalRetrievalError(GoalServiceError):
    """Raised when goal retrieval fails"""
    def __init__(self, detail: str = "Failed to retrieve goals"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_RETRIEVAL_FAILED")


class GoalStatisticsError(GoalServiceError):
    """Raised when goal statistics retrieval fails"""
    def __init__(self, detail: str = "Failed to get goal statistics"):
        super().__init__(detail=detail, status_code=422, error_code="GOAL_STATISTICS_FAILED")


class MilestoneCreationError(GoalServiceError):
    """Raised when milestone creation fails"""
    def __init__(self, detail: str = "Failed to create milestone"):
        super().__init__(detail=detail, status_code=422, error_code="MILESTONE_CREATION_FAILED")


class MilestoneRetrievalError(GoalServiceError):
    """Raised when milestone retrieval fails"""
    def __init__(self, detail: str = "Failed to retrieve milestones"):
        super().__init__(detail=detail, status_code=422, error_code="MILESTONE_RETRIEVAL_FAILED")


class MilestoneProgressUpdateError(GoalServiceError):
    """Raised when milestone progress update fails"""
    def __init__(self, detail: str = "Failed to update milestone progress"):
        super().__init__(detail=detail, status_code=422, error_code="MILESTONE_PROGRESS_UPDATE_FAILED")

class GoalLimitExceededError(GoalValidationError):
    """Raised when user exceeds goal limit"""
    def __init__(self, current_count: int, limit: int):
        super().__init__(
            detail=f"Goal limit exceeded. You have {current_count} goals but your plan allows only {limit} goals."
        )


class GoalReadOnlyExcessError(GoalServiceError):
    """Raised when goal exceeds plan limit and is read-only"""
    def __init__(self, goal_id: int, current_count: int, limit: int):
        super().__init__(
            detail=f"This goal is read-only. You have {current_count} goals but your plan allows {limit}. Upgrade or delete excess goals.",
            status_code=403,
            error_code="RECORD_READ_ONLY_EXCESS"
        )
        self.goal_id = goal_id
        self.current_count = current_count
        self.limit = limit
