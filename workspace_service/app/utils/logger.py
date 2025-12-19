import sys
import os
from typing import Optional

# Add the logging directory to the path
sys.path.append('/app/logging')

try:
    from logging_utils import get_structured_logger, set_request_context
except ImportError:
    # Fallback for local development
    import logging

    def get_structured_logger(name: str, service_name: str, level: str = "INFO"):
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            logger.addHandler(handler)
        return logger

    def set_request_context(request_id: str, user_id: Optional[int] = None, service_name: Optional[str] = None):
        pass


def get_logger(name: str):
    """Get a structured logger instance for backward compatibility"""
    return get_structured_logger(name, "workspace_service")


def log_security_event(logger, event: str, user_id: Optional[int] = None, details: Optional[str] = None):
    """Log security-related events"""
    if hasattr(logger, 'log_security_event'):
        logger.log_security_event(event, user_id, details)
    else:
        logger.warning(f"Security event: {event} - User: {user_id} - Details: {details}")


def log_operation(logger, operation: str, user_id: int, details: Optional[str] = None):
    """Log business operations for audit trail"""
    if hasattr(logger, 'log_business_operation'):
        logger.log_business_operation(operation, user_id, details=details)
    else:
        logger.info(f"Operation: {operation} - User: {user_id} - Details: {details}")

