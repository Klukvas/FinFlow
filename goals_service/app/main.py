from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import goal, internal
from app.exception_handlers import (
    goal_not_found_handler, goal_validation_handler, goal_ownership_handler,
    milestone_not_found_handler, milestone_validation_handler, goal_progress_handler,
    http_exception_handler, general_exception_handler
)
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalOwnershipError,
    MilestoneNotFoundError, MilestoneValidationError, GoalProgressError
)
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

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
app.add_exception_handler(MilestoneNotFoundError, milestone_not_found_handler)
app.add_exception_handler(MilestoneValidationError, milestone_validation_handler)
app.add_exception_handler(GoalProgressError, goal_progress_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(goal.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(internal.internal_router, prefix="/internal", tags=["internal"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
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
