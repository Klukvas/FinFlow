from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine
from app.routers.dept_route import router as debt_router
from app.routers.contact import router as contact_router
from app.config import settings
from app.utils.logger import get_logger
from app.exceptions import (
    DebtServiceException,
    DebtNotFoundError,
    ContactNotFoundError,
    PaymentNotFoundError,
    DebtValidationError,
    ContactValidationError,
    PaymentValidationError,
    DebtAmountError,
    PaymentAmountError,
    DebtDateError,
    ExternalServiceError,
    DatabaseError,
    ContactHasAssociatedDebtsError,
    DebtCreationFailedError,
    DebtUpdateFailedError,
    DebtDeletionFailedError,
    ContactCreationFailedError,
    ContactUpdateFailedError,
    ContactDeletionFailedError,
    PaymentCreationFailedError,
    InvalidDebtTypeError,
    InvalidPaymentMethodError,
    DebtReadOnlyExcessError
)
from app.schemas.error import ErrorResponse
import time
import uuid

# Import models to ensure they are registered with Base
from app.models.debt import Debt, Contact, DebtPayment

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
        from app.utils.logger import set_request_context
        set_request_context(request_id, user_id, "debt_service")
        
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



app = FastAPI(
    title="Debt Service",
    description="Microservice for managing user debts, contacts, and debt payments with workspace support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True}
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(debt_router, prefix="/debts", tags=["debts"])
app.include_router(contact_router, prefix="/contacts", tags=["contacts"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "debt-service",
        "version": app.version
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Debt Service API",
        "version": app.version,
        "docs": "/docs"
    }

# Exception handlers
@app.exception_handler(DebtServiceException)
async def debt_service_exception_handler(request: Request, exc: DebtServiceException):
    """Handle debt service exceptions with unified error format"""
    logger.error(f"Debt service error: {exc.message}")
    
    # Determine status code based on error type
    status_code = 400  # Default to bad request
    if isinstance(exc, (DebtNotFoundError, ContactNotFoundError, PaymentNotFoundError)):
        status_code = 404
    elif isinstance(exc, (DebtValidationError, ContactValidationError, PaymentValidationError, 
                         DebtAmountError, PaymentAmountError, DebtDateError,
                         ContactHasAssociatedDebtsError, InvalidDebtTypeError, InvalidPaymentMethodError)):
        status_code = 400
    elif isinstance(exc, (DebtCreationFailedError, DebtUpdateFailedError, DebtDeletionFailedError,
                         ContactCreationFailedError, ContactUpdateFailedError, ContactDeletionFailedError,
                         PaymentCreationFailedError)):
        status_code = 422
    elif isinstance(exc, DebtReadOnlyExcessError):
        status_code = 403
    elif isinstance(exc, (ExternalServiceError, DatabaseError)):
        status_code = 500
    
    error_response = ErrorResponse(
        error=exc.message,
        errorCode=exc.error_code,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    
    error_response = ErrorResponse(
        error="Request validation failed",
        errorCode="VALIDATION_ERROR",
        details={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error: {exc}")
    
    error_response = ErrorResponse(
        error="Database operation failed",
        errorCode="DATABASE_ERROR"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

def custom_openapi():
    """Custom OpenAPI schema with workspace and bearer auth"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        },
        "WorkspaceId": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Workspace-Id",
            "description": "Enter your workspace UUID"
        }
    }
    
    # Apply security to all non-internal endpoints
    for path, path_item in openapi_schema["paths"].items():
        if not path.startswith("/internal") and not path.startswith("/health"):
            for method in path_item:
                if method in ["get", "post", "put", "patch", "delete"]:
                    path_item[method]["security"] = [
                        {"BearerAuth": [], "WorkspaceId": []}
                    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,  # Different port for debt service
        reload=settings.debug
    )
