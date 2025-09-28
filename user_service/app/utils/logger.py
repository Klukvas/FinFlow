import logging
from typing import Optional
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with consistent configuration"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    return logger

def log_security_event(logger: logging.Logger, event: str, user_id: Optional[int] = None, details: Optional[str] = None):
    """Log security-related events"""
    message = f"SECURITY: {event}"
    if user_id:
        message += f" | User ID: {user_id}"
    if details:
        message += f" | Details: {details}"
    logger.warning(message)

def log_operation(logger: logging.Logger, operation: str, user_id: int, details: Optional[str] = None):
    """Log business operations for audit trail"""
    message = f"OPERATION: {operation} | User ID: {user_id}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)

def log_authentication_attempt(logger: logging.Logger, email: str, success: bool, details: Optional[str] = None):
    """Log authentication attempts"""
    status = "SUCCESS" if success else "FAILED"
    message = f"AUTH_ATTEMPT: {status} | Email: {email}"
    if details:
        message += f" | Details: {details}"
    if success:
        logger.info(message)
    else:
        logger.warning(message)

