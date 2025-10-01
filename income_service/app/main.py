from fastapi import FastAPI, HTTPException
from app.routers import income, internal
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    income_not_found_handler,
    income_validation_handler,
    income_amount_handler,
    income_date_handler,
    income_description_handler,
    external_service_handler,
    http_exception_handler
)
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Import models to ensure they are registered with Base
from app.models.income import Income

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Income Service",
    description="Microservice for managing user incomes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(IncomeNotFoundError, income_not_found_handler)
app.add_exception_handler(IncomeValidationError, income_validation_handler)
app.add_exception_handler(IncomeAmountError, income_amount_handler)
app.add_exception_handler(IncomeDateError, income_date_handler)
app.add_exception_handler(IncomeDescriptionError, income_description_handler)
app.add_exception_handler(ExternalServiceError, external_service_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(income.router)
app.include_router(internal.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "income-service"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Income Service API", "version": "1.0.0"}
