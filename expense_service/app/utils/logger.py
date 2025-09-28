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

def log_operation(logger: logging.Logger, operation: str, user_id: int, expense_id: Optional[int] = None, details: Optional[str] = None):
    """Log business operations for audit trail"""
    message = f"OPERATION: {operation} | User ID: {user_id}"
    if expense_id:
        message += f" | Expense ID: {expense_id}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)

def log_external_service_call(logger: logging.Logger, service: str, endpoint: str, status_code: int, duration: Optional[float] = None):
    """Log external service calls for monitoring"""
    message = f"EXTERNAL_SERVICE: {service} | Endpoint: {endpoint} | Status: {status_code}"
    if duration:
        message += f" | Duration: {duration:.3f}s"
    logger.info(message)

