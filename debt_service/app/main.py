from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine
from app.routers.dept_route import router as debt_router
from app.routers.contact import router as contact_router
from app.config import settings
from app.utils.logger import get_logger

# Import models to ensure they are registered with Base
from app.models.debt import Debt, Contact, DebtPayment

logger = get_logger(__name__)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")
    raise

app = FastAPI(
    title="Debt Service",
    description="Microservice for managing user debts, contacts, and debt payments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debt_router, prefix="/debts", tags=["debts"])
app.include_router(contact_router, prefix="/contacts", tags=["contacts"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "debt_service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Debt Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return HTTPException(
        status_code=422,
        detail=f"Validation error: {exc.errors()}"
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request, exc):
    """Handle database errors"""
    logger.error(f"Database error: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,  # Different port for debt service
        reload=settings.debug
    )
