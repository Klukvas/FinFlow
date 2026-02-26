"""
Shared logger factory for all microservices.

Replaces per-service app/utils/logger.py wrappers.
Usage:
    from shared.logging import get_logger
    logger = get_logger(__name__)
"""

from typing import Optional

from shared.logging.logging_utils import (
    get_structured_logger,
    StructuredLogger,
    set_request_context,
    clear_request_context,
    generate_request_id,
)

# Module-level service name, set once at service startup
_service_name: str = "unknown"


def configure(service_name: str) -> None:
    """Configure the shared logger with a service name. Call once at startup."""
    global _service_name
    _service_name = service_name


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance for the configured service."""
    return get_structured_logger(name, _service_name)


def log_security_event(
    logger: StructuredLogger,
    event: str,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    """Log security-related events."""
    logger.log_security_event(event, user_id, details)


def log_operation(
    logger: StructuredLogger,
    operation: str,
    user_id: int,
    details: Optional[str] = None,
) -> None:
    """Log business operations for audit trail."""
    logger.log_business_operation(operation, user_id, details=details)


def log_authentication_attempt(
    logger: StructuredLogger,
    email: str,
    success: bool,
    details: Optional[str] = None,
) -> None:
    """Log authentication attempts."""
    logger.log_authentication(email, success, details)


def log_external_service_call(
    logger: StructuredLogger,
    service_name: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    **kwargs,
) -> None:
    """Log external service calls for monitoring."""
    logger.log_external_service_call(
        service=service_name,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
    )
