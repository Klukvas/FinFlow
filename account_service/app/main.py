from fastapi import FastAPI, HTTPException
from app.routers import account, internal
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    account_not_found_handler,
    account_validation_handler,
    account_ownership_handler,
    account_archived_handler,
    account_balance_handler,
    external_service_handler,
    http_exception_handler
)
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    ExternalServiceError
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Account Service",
    description="Microservice for managing user accounts with transaction integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(AccountNotFoundError, account_not_found_handler)
app.add_exception_handler(AccountValidationError, account_validation_handler)
app.add_exception_handler(AccountOwnershipError, account_ownership_handler)
app.add_exception_handler(AccountArchivedError, account_archived_handler)
app.add_exception_handler(AccountBalanceError, account_balance_handler)
app.add_exception_handler(ExternalServiceError, external_service_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(account.router)
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
    return {"status": "healthy", "service": "account-service"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Account Service API", "version": "1.0.0"}

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Account Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Account Service shutting down...")
