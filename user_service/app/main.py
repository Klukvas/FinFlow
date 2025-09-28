from fastapi import FastAPI, HTTPException
from app.routers import auth
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import (
    custom_validation_exception_handler,
    user_not_found_handler,
    user_validation_handler,
    user_authentication_handler,
    user_registration_handler,
    password_policy_handler,
    username_policy_handler,
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
    UsernamePolicyError,
    AccountLockedError,
    RateLimitError
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Service",
    description="Microservice for user authentication and management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserValidationError, user_validation_handler)
app.add_exception_handler(UserAuthenticationError, user_authentication_handler)
app.add_exception_handler(UserRegistrationError, user_registration_handler)
app.add_exception_handler(PasswordPolicyError, password_policy_handler)
app.add_exception_handler(UsernamePolicyError, username_policy_handler)
app.add_exception_handler(AccountLockedError, account_locked_handler)
app.add_exception_handler(RateLimitError, rate_limit_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(auth.router)

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
    return {"status": "healthy", "service": "user-service"}

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("User Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("User Service shutting down...")