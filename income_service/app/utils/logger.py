import logging
import sys
from typing import Optional
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    return logger

def log_security_event(logger: logging.Logger, event: str, user_id: Optional[int] = None, details: str = ""):
    """Log security-related events"""
    message = f"SECURITY: {event}"
    if user_id:
        message += f" | User: {user_id}"
    if details:
        message += f" | Details: {details}"
    logger.warning(message)

def log_external_service_call(logger: logging.Logger, service_url: str, endpoint: str, status_code: int, duration: float):
    """Log external service calls"""
    logger.info(f"External service call: {service_url}{endpoint} | Status: {status_code} | Duration: {duration:.3f}s")
