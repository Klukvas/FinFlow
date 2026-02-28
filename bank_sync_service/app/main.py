from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine
from app.routers.connections import router as connections_router
from app.routers.sync import router as sync_router
from app.routers.webhook import router as webhook_router
from app.routers.internal import router as internal_router
from app.config import settings
from app.utils.logger import get_logger
from app.exceptions import (
    BankSyncException,
    ConnectionNotFoundError,
    LinkedAccountNotFoundError,
    SyncLogNotFoundError,
    TokenValidationError,
    MonobankApiError,
    RateLimitError,
    EncryptionError,
    SyncInProgressError,
    AccountNotLinkedError,
    ExternalServiceError,
    DatabaseError,
)
from app.schemas.error import ErrorResponse
import time
import uuid

# Import models to ensure they are registered with Base
from app.models.bank_connection import BankConnection
from app.models.linked_account import LinkedAccount
from app.models.sync_log import SyncLog
from app.models.synced_transaction import SyncedTransaction

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())

        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        from app.utils.logger import set_request_context
        set_request_context(request_id, user_id, "bank_sync_service")

        start_time = time.time()
        logger.log_api_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=0,
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            logger.log_api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=request_id,
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
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
                request_id=request_id,
            )
            raise


app = FastAPI(
    title="Bank Sync Service",
    description="Microservice for synchronizing bank transactions (Monobank) with FinFlow",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    swagger_ui_parameters={"persistAuthorization": True} if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(connections_router, prefix="/connections", tags=["connections"])
app.include_router(sync_router, prefix="/connections", tags=["sync"])
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
app.include_router(internal_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "bank-sync-service",
        "version": app.version,
    }


@app.get("/")
async def root():
    return {
        "message": "Bank Sync Service API",
        "version": app.version,
        "docs": "/docs",
    }


# Exception handlers
@app.exception_handler(BankSyncException)
async def bank_sync_exception_handler(request: Request, exc: BankSyncException):
    logger.error(f"Bank sync error: {exc.message}")

    status_code = 400
    if isinstance(exc, (ConnectionNotFoundError, LinkedAccountNotFoundError, SyncLogNotFoundError)):
        status_code = 404
    elif isinstance(exc, (TokenValidationError, AccountNotLinkedError)):
        status_code = 400
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, SyncInProgressError):
        status_code = 409
    elif isinstance(exc, EncryptionError):
        status_code = 500
    elif isinstance(exc, MonobankApiError):
        status_code = 502
    elif isinstance(exc, (ExternalServiceError, DatabaseError)):
        status_code = 500

    error_response = ErrorResponse(
        error=exc.message,
        errorCode=exc.error_code,
        details=exc.details,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")

    error_response = ErrorResponse(
        error="Request validation failed",
        errorCode="VALIDATION_ERROR",
        details={"errors": exc.errors()},
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")

    error_response = ErrorResponse(
        error="Database operation failed",
        errorCode="DATABASE_ERROR",
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token",
        },
        "WorkspaceId": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Workspace-Id",
            "description": "Enter your workspace UUID",
        },
    }

    for path, path_item in openapi_schema["paths"].items():
        if not path.startswith("/internal") and not path.startswith("/health") and not path.startswith("/webhook"):
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
        port=8016,
        reload=settings.DEBUG,
    )
