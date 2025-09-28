from fastapi import FastAPI, HTTPException
from app.routers import category, internal
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    category_not_found_handler,
    category_validation_handler,
    category_ownership_handler,
    circular_relationship_handler,
    category_depth_handler,
    category_name_conflict_handler,
    http_exception_handler
)
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryOwnershipError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Category Service",
    description="Microservice for managing hierarchical categories",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(CategoryNotFoundError, category_not_found_handler)
app.add_exception_handler(CategoryValidationError, category_validation_handler)
app.add_exception_handler(CategoryOwnershipError, category_ownership_handler)
app.add_exception_handler(CircularRelationshipError, circular_relationship_handler)
app.add_exception_handler(CategoryDepthExceededError, category_depth_handler)
app.add_exception_handler(CategoryNameConflictError, category_name_conflict_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(category.router)
app.include_router(internal.internal_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "category-service"}

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Category Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Category Service shutting down...")