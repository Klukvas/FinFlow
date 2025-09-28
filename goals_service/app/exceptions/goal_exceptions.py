from fastapi import HTTPException
from typing import Any, Dict, Optional


class GoalServiceError(HTTPException):
    """Base exception for goal service errors"""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class GoalNotFoundError(GoalServiceError):
    """Raised when a goal is not found"""
    def __init__(self, detail: str = "Goal not found"):
        super().__init__(detail=detail, status_code=404)


class GoalValidationError(GoalServiceError):
    """Raised when goal validation fails"""
    def __init__(self, detail: str = "Goal validation failed"):
        super().__init__(detail=detail, status_code=422)


class GoalOwnershipError(GoalServiceError):
    """Raised when user doesn't own the goal"""
    def __init__(self, detail: str = "Access denied to goal"):
        super().__init__(detail=detail, status_code=403)


class MilestoneNotFoundError(GoalServiceError):
    """Raised when a milestone is not found"""
    def __init__(self, detail: str = "Milestone not found"):
        super().__init__(detail=detail, status_code=404)


class MilestoneValidationError(GoalServiceError):
    """Raised when milestone validation fails"""
    def __init__(self, detail: str = "Milestone validation failed"):
        super().__init__(detail=detail, status_code=422)


class GoalProgressError(GoalServiceError):
    """Raised when goal progress update fails"""
    def __init__(self, detail: str = "Failed to update goal progress"):
        super().__init__(detail=detail, status_code=422)
