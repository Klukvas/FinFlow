from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import goal, internal
from app.exception_handlers import (
    goal_not_found_handler, goal_validation_handler, goal_ownership_handler,
    goal_creation_handler, goal_update_handler, goal_deletion_handler,
    goal_retrieval_handler, goal_statistics_handler, goal_progress_handler,
    milestone_not_found_handler, milestone_validation_handler, milestone_creation_handler,
    milestone_retrieval_handler, milestone_progress_update_handler,
    http_exception_handler, general_exception_handler
)
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalOwnershipError, GoalCreationError,
    GoalUpdateError, GoalDeletionError, GoalRetrievalError, GoalStatisticsError,
    GoalProgressError, MilestoneNotFoundError, MilestoneValidationError,
    MilestoneCreationError, MilestoneRetrievalError, MilestoneProgressUpdateError
)
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger
import time
import uuid

logger = get_logger(__name__)
# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract user ID from request if available
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Set request context
        from logging_utils import set_request_context
        set_request_context(request_id, user_id, "goals_service")
        
        # Log request start
        start_time = time.time()
        logger.log_api_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=0,  # Will be updated after response
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.log_api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error response
            logger.error(
                f"API request failed: {request.method} {request.url.path} - {str(e)}",
                category="api",
                operation="api_request_error",
                method=request.method,
                endpoint=str(request.url.path),
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=request_id
            )
            
            raise



# Database tables are created via alembic migrations
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Microservice for managing financial goals and milestones",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(GoalNotFoundError, goal_not_found_handler)
app.add_exception_handler(GoalValidationError, goal_validation_handler)
app.add_exception_handler(GoalOwnershipError, goal_ownership_handler)
app.add_exception_handler(GoalCreationError, goal_creation_handler)
app.add_exception_handler(GoalUpdateError, goal_update_handler)
app.add_exception_handler(GoalDeletionError, goal_deletion_handler)
app.add_exception_handler(GoalRetrievalError, goal_retrieval_handler)
app.add_exception_handler(GoalStatisticsError, goal_statistics_handler)
app.add_exception_handler(GoalProgressError, goal_progress_handler)
app.add_exception_handler(MilestoneNotFoundError, milestone_not_found_handler)
app.add_exception_handler(MilestoneValidationError, milestone_validation_handler)
app.add_exception_handler(MilestoneCreationError, milestone_creation_handler)
app.add_exception_handler(MilestoneRetrievalError, milestone_retrieval_handler)
app.add_exception_handler(MilestoneProgressUpdateError, milestone_progress_update_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(goal.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(internal.internal_router, prefix="/internal", tags=["internal"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Goals Service",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "goals_service",
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
