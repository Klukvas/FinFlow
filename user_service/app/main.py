from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import auth, logging, internal, admin, support
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    user_not_found_handler,
    user_validation_handler,
    user_authentication_handler,
    user_registration_handler,
    password_policy_handler,
    account_locked_handler,
    rate_limit_handler,
    http_exception_handler
)
from app.exceptions.user_errors import (
    UserNotFoundError,
    UserValidationError,
    UserAuthenticationError,
    UserRegistrationError,
    PasswordPolicyError,
    AccountLockedError,
    RateLimitError
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from shared.geoip import GeoIPMiddleware
from shared.sentry import init_sentry
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger
import time
import uuid

init_sentry("user_service")

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
        set_request_context(request_id, user_id, "user_service")
        
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
    """Application lifespan event handler"""
    logger.info(
        "User Service starting up",
        category="application",
        operation="service_startup",
        service_name="user_service",
        version="2.0.0",
        workspace_service_url=settings.WORKSPACE_SERVICE_URL,
        has_internal_token=bool(settings.INTERNAL_SECRET_TOKEN),
        token_length=len(settings.INTERNAL_SECRET_TOKEN) if settings.INTERNAL_SECRET_TOKEN else 0
    )
    yield
    logger.info(
        "User Service shutting down",
        category="application",
        operation="service_shutdown",
        service_name="user_service"
    )

app = FastAPI(
    title="User Service",
    description="Microservice for user authentication and management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserValidationError, user_validation_handler)
app.add_exception_handler(UserAuthenticationError, user_authentication_handler)
app.add_exception_handler(UserRegistrationError, user_registration_handler)
app.add_exception_handler(PasswordPolicyError, password_policy_handler)
app.add_exception_handler(AccountLockedError, account_locked_handler)
app.add_exception_handler(RateLimitError, rate_limit_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(logging.router)
app.include_router(internal.router)
app.include_router(admin.router)
app.include_router(support.router, prefix="/v1")

# Middleware order matters! Added LAST = runs FIRST
# 1. RequestLoggingMiddleware (added first, runs last)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GeoIPMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 2. CORS (added last, runs first - handles preflight OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}

