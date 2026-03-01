from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
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
    account_read_only_excess_handler,
    external_service_handler,
    http_exception_handler
)
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    AccountReadOnlyExcessError,
    ExternalServiceError,
    AccountErrorCode
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from shared.geoip import GeoIPMiddleware
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
        from app.utils.logger import set_request_context
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info("Account Service starting up...")
    yield
    logger.info("Account Service shutting down...")

app = FastAPI(
    title="Account Service",
    description="Microservice for managing user accounts with workspace support and transaction integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(AccountNotFoundError, account_not_found_handler)
app.add_exception_handler(AccountValidationError, account_validation_handler)
app.add_exception_handler(AccountOwnershipError, account_ownership_handler)
app.add_exception_handler(AccountArchivedError, account_archived_handler)
app.add_exception_handler(AccountBalanceError, account_balance_handler)
app.add_exception_handler(AccountReadOnlyExcessError, account_read_only_excess_handler)
app.add_exception_handler(ExternalServiceError, external_service_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GeoIPMiddleware)
app.add_middleware(GZIPMiddleware, minimum_size=500)

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
    return {"message": "Account Service API", "version": app.version}

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
