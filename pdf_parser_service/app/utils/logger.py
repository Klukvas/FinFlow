import sys
import os
from typing import Optional

# Add the logging directory to the path
sys.path.append('/app/logging')

from logging_utils import get_structured_logger

def get_logger(name: str):
    """Get a structured logger instance for backward compatibility"""
    return get_structured_logger(name, "pdf_parser_service")

# Keep existing specialized functions for backward compatibility
def log_security_event(logger, event: str, user_id: Optional[int] = None, details: Optional[str] = None):
    """Log security-related events"""
    logger.log_security_event(event, user_id, details)

def log_operation(logger, operation: str, user_id: int, details: Optional[str] = None):
    """Log business operations for audit trail"""
    logger.log_business_operation(
        operation, 
        user_id, 
        details=details
    )

def log_authentication_attempt(logger, email: str, success: bool, details: Optional[str] = None):
    """Log authentication attempts"""
    if success:
        logger.info(
            f"Authentication successful for {email}",
            category="security",
            operation="auth_success",
            email=email,
            details=details
        )
    else:
        logger.warning(
            f"Authentication failed for {email}",
            category="security",
            operation="auth_failure",
            email=email,
            details=details
        )
