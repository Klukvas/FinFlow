"""Logging utilities for account_service."""

import shared.logging.logger as _shared_logger

# Configure shared logger with this service's name
_shared_logger.configure("account_service")

# Re-export shared logging functions
from shared.logging.logger import (
    get_logger,
    log_security_event,
    log_operation,
    log_authentication_attempt,
    log_external_service_call,
)
from shared.logging.logging_utils import (
    set_request_context,
    clear_request_context,
    generate_request_id,
)

__all__ = [
    "get_logger",
    "log_security_event",
    "log_operation",
    "log_authentication_attempt",
    "log_external_service_call",
    "set_request_context",
    "clear_request_context",
    "generate_request_id",
]
