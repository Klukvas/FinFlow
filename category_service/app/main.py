from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import category, internal, mcc
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    category_exception_handler,
    http_exception_handler,
    general_exception_handler
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
from starlette.middleware.gzip import GZipMiddleware
from shared.geoip import GeoIPMiddleware
from shared.sentry import init_sentry
from app.config import settings
from app.utils.logger import get_logger
import time
import uuid

init_sentry("category_service")

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
        set_request_context(request_id, user_id, "category_service")
        
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
    logger.info(
        "Category Service starting up",
        category="application",
        operation="service_startup",
        service_name="category_service",
        version="2.0.0"
    )
    yield
    logger.info(
        "Category Service shutting down",
        category="application",
        operation="service_shutdown",
        service_name="category_service"
    )

app = FastAPI(
    title="Category Service",
    description="Microservice for managing hierarchical categories",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True
    },
    lifespan=lifespan
)

# Configure JWT Bearer authentication for Swagger UI
from fastapi.openapi.models import SecurityScheme
from fastapi.security import HTTPBearer

security_scheme = HTTPBearer()

app.openapi_schema = None  # Reset to force regeneration

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
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
            "description": "Enter your JWT token (no 'Bearer' prefix needed)"
        },
        "WorkspaceId": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Workspace-Id",
            "description": "Workspace UUID for multi-tenancy"
        }
    }
    
    # Apply security to all endpoints except health and internal
    for path, path_item in openapi_schema["paths"].items():
        # Skip internal endpoints and health check
        if path.startswith("/internal") or path == "/health":
            continue
        
        # Apply security to all methods
        for method in path_item:
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if "security" not in path_item[method]:
                    # Most endpoints require both JWT and Workspace-Id
                    # Statistics endpoint also requires workspace
                    path_item[method]["security"] = [
                        {"BearerAuth": [], "WorkspaceId": []}
                    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Register exception handlers (order matters - most specific first)
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(CategoryNotFoundError, category_exception_handler)
app.add_exception_handler(CategoryValidationError, category_exception_handler)
app.add_exception_handler(CategoryOwnershipError, category_exception_handler)
app.add_exception_handler(CircularRelationshipError, category_exception_handler)
app.add_exception_handler(CategoryDepthExceededError, category_exception_handler)
app.add_exception_handler(CategoryNameConflictError, category_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)  # Catch-all for unexpected errors

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GeoIPMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Include routers
app.include_router(category.router)
app.include_router(mcc.router)
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

