from fastapi import FastAPI, HTTPException, Request
from app.routers import account, internal
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
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
        set_request_context(request_id, user_id, "account_service")
        
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

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

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
