from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from app.exceptions.workspace_errors import (
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
    WorkspaceErrorCode,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with improved error messages"""
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "Validation error", "errorCode": WorkspaceErrorCode.VALIDATION_ERROR}
        )

    first_error = errors[0]
    field = first_error["loc"][-1] if first_error["loc"] else "field"
    error_type = first_error["type"]
    error_msg = first_error.get("msg", "Invalid value")

    if error_type == "missing":
        message = f"{field.capitalize()} is required"
    elif error_type == "string_too_short":
        message = f"{field.capitalize()} must be at least {first_error.get('ctx', {}).get('min_length', '')} characters long"
    elif error_type == "string_too_long":
        message = f"{field.capitalize()} must be no more than {first_error.get('ctx', {}).get('max_length', '')} characters long"
    elif error_type == "value_error":
        message = error_msg
    else:
        message = f"{field.capitalize()}: {error_msg}"

    logger.warning(f"Validation error: {message} for field {field}")

    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": message, "errorCode": WorkspaceErrorCode.VALIDATION_ERROR}
    )


async def workspace_not_found_handler(request: Request, exc: WorkspaceNotFoundError):
    """Handle workspace not found errors"""
    logger.info(f"Workspace not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def workspace_validation_handler(request: Request, exc: WorkspaceValidationError):
    """Handle workspace validation errors"""
    logger.warning(f"Workspace validation error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def workspace_access_denied_handler(request: Request, exc: WorkspaceAccessDeniedError):
    """Handle workspace access denied errors"""
    logger.warning(f"Workspace access denied: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def workspace_archived_handler(request: Request, exc: WorkspaceArchivedError):
    """Handle workspace archived errors"""
    logger.warning(f"Workspace archived: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def member_not_found_handler(request: Request, exc: MemberNotFoundError):
    """Handle member not found errors"""
    logger.info(f"Member not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def member_already_exists_handler(request: Request, exc: MemberAlreadyExistsError):
    """Handle member already exists errors"""
    logger.warning(f"Member already exists: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def invalid_role_change_handler(request: Request, exc: InvalidRoleChangeError):
    """Handle invalid role change errors"""
    logger.warning(f"Invalid role change: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def owner_cannot_leave_handler(request: Request, exc: OwnerCannotLeaveError):
    """Handle owner cannot leave errors"""
    logger.warning(f"Owner cannot leave: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def invite_not_found_handler(request: Request, exc: InviteNotFoundError):
    """Handle invite not found errors"""
    logger.info(f"Invite not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def invite_expired_handler(request: Request, exc: InviteExpiredError):
    """Handle invite expired errors"""
    logger.info(f"Invite expired: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def invite_already_used_handler(request: Request, exc: InviteAlreadyUsedError):
    """Handle invite already used errors"""
    logger.info(f"Invite already used: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def invalid_invite_token_handler(request: Request, exc: InvalidInviteTokenError):
    """Handle invalid invite token errors"""
    logger.warning(f"Invalid invite token: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": exc.error_code}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle general HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "errorCode": WorkspaceErrorCode.INTERNAL_ERROR}
    )

