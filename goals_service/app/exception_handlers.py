from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalOwnershipError,
    MilestoneNotFoundError, MilestoneValidationError, GoalProgressError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def goal_not_found_handler(request: Request, exc: GoalNotFoundError):
    """Handle goal not found errors"""
    logger.warning(f"Goal not found: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content={"error": "Goal not found", "detail": exc.detail}
    )


async def goal_validation_handler(request: Request, exc: GoalValidationError):
    """Handle goal validation errors"""
    logger.warning(f"Goal validation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": exc.detail}
    )


async def goal_ownership_handler(request: Request, exc: GoalOwnershipError):
    """Handle goal ownership errors"""
    logger.warning(f"Goal ownership error: {exc.detail}")
    return JSONResponse(
        status_code=403,
        content={"error": "Access denied", "detail": exc.detail}
    )


async def milestone_not_found_handler(request: Request, exc: MilestoneNotFoundError):
    """Handle milestone not found errors"""
    logger.warning(f"Milestone not found: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content={"error": "Milestone not found", "detail": exc.detail}
    )


async def milestone_validation_handler(request: Request, exc: MilestoneValidationError):
    """Handle milestone validation errors"""
    logger.warning(f"Milestone validation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": exc.detail}
    )


async def goal_progress_handler(request: Request, exc: GoalProgressError):
    """Handle goal progress errors"""
    logger.warning(f"Goal progress error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": "Progress update failed", "detail": exc.detail}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Request failed", "detail": exc.detail}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )
