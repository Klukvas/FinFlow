from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalOwnershipError, GoalCreationError,
    GoalUpdateError, GoalDeletionError, GoalRetrievalError, GoalStatisticsError,
    GoalProgressError, MilestoneNotFoundError, MilestoneValidationError,
    MilestoneCreationError, MilestoneRetrievalError, MilestoneProgressUpdateError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def goal_not_found_handler(request: Request, exc: GoalNotFoundError):
    """Handle goal not found errors"""
    logger.warning(f"Goal not found: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_validation_handler(request: Request, exc: GoalValidationError):
    """Handle goal validation errors"""
    logger.warning(f"Goal validation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_ownership_handler(request: Request, exc: GoalOwnershipError):
    """Handle goal ownership errors"""
    logger.warning(f"Goal ownership error: {exc.detail}")
    return JSONResponse(
        status_code=403,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def milestone_not_found_handler(request: Request, exc: MilestoneNotFoundError):
    """Handle milestone not found errors"""
    logger.warning(f"Milestone not found: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def milestone_validation_handler(request: Request, exc: MilestoneValidationError):
    """Handle milestone validation errors"""
    logger.warning(f"Milestone validation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_progress_handler(request: Request, exc: GoalProgressError):
    """Handle goal progress errors"""
    logger.warning(f"Goal progress error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": "HTTP_REQUEST_FAILED"}
    )


async def goal_creation_handler(request: Request, exc: GoalCreationError):
    """Handle goal creation errors"""
    logger.warning(f"Goal creation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_update_handler(request: Request, exc: GoalUpdateError):
    """Handle goal update errors"""
    logger.warning(f"Goal update error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_deletion_handler(request: Request, exc: GoalDeletionError):
    """Handle goal deletion errors"""
    logger.warning(f"Goal deletion error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_retrieval_handler(request: Request, exc: GoalRetrievalError):
    """Handle goal retrieval errors"""
    logger.warning(f"Goal retrieval error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def goal_statistics_handler(request: Request, exc: GoalStatisticsError):
    """Handle goal statistics errors"""
    logger.warning(f"Goal statistics error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def milestone_creation_handler(request: Request, exc: MilestoneCreationError):
    """Handle milestone creation errors"""
    logger.warning(f"Milestone creation error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def milestone_retrieval_handler(request: Request, exc: MilestoneRetrievalError):
    """Handle milestone retrieval errors"""
    logger.warning(f"Milestone retrieval error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def milestone_progress_update_handler(request: Request, exc: MilestoneProgressUpdateError):
    """Handle milestone progress update errors"""
    logger.warning(f"Milestone progress update error: {exc.detail}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "errorCode": "INTERNAL_SERVER_ERROR"}
    )
