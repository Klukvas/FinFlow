from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    workspaces_router,
    members_router,
    invites_router,
    internal_router,
)
from app.exception_handlers import (
    custom_validation_exception_handler,
    workspace_not_found_handler,
    workspace_validation_handler,
    workspace_access_denied_handler,
    workspace_archived_handler,
    member_not_found_handler,
    member_already_exists_handler,
    invalid_role_change_handler,
    owner_cannot_leave_handler,
    invite_not_found_handler,
    invite_expired_handler,
    invite_already_used_handler,
    invalid_invite_token_handler,
    http_exception_handler,
)
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
    InvalidRoleChangeError,
    OwnerCannotLeaveError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteAlreadyUsedError,
    InvalidInviteTokenError,
)
from app.database import Base, engine
from app.config import settings
from app.utils.logger import get_logger
import time
import uuid

logger = get_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        user_id = None

        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id

        from app.utils.logger import get_logger
        try:
            from logging_utils import set_request_context
            set_request_context(request_id, user_id, "workspace_service")
        except ImportError:
            pass

        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            if hasattr(logger, 'log_api_request'):
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
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"API request failed: {request.method} {request.url.path} - {str(e)}"
            )
            raise


app = FastAPI(
    title="Workspace Service",
    description="Microservice for workspace and group management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(WorkspaceNotFoundError, workspace_not_found_handler)
app.add_exception_handler(WorkspaceValidationError, workspace_validation_handler)
app.add_exception_handler(WorkspaceAccessDeniedError, workspace_access_denied_handler)
app.add_exception_handler(WorkspaceArchivedError, workspace_archived_handler)
app.add_exception_handler(MemberNotFoundError, member_not_found_handler)
app.add_exception_handler(MemberAlreadyExistsError, member_already_exists_handler)
app.add_exception_handler(InvalidRoleChangeError, invalid_role_change_handler)
app.add_exception_handler(OwnerCannotLeaveError, owner_cannot_leave_handler)
app.add_exception_handler(InviteNotFoundError, invite_not_found_handler)
app.add_exception_handler(InviteExpiredError, invite_expired_handler)
app.add_exception_handler(InviteAlreadyUsedError, invite_already_used_handler)
app.add_exception_handler(InvalidInviteTokenError, invalid_invite_token_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(workspaces_router)
app.include_router(members_router)
app.include_router(invites_router)
app.include_router(internal_router)

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
    return {"status": "healthy", "service": "workspace-service"}


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Workspace Service starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Workspace Service shutting down")

