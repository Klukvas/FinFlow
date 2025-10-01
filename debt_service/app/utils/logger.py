import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debt_service.log')
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def log_security_event(logger: logging.Logger, event: str, user_id: Optional[int] = None, details: Optional[str] = None):
    """Log security-related events"""
    message = f"SECURITY: {event}"
    if user_id:
        message += f" | User ID: {user_id}"
    if details:
        message += f" | Details: {details}"
    logger.warning(message)

def log_operation(logger: logging.Logger, operation: str, user_id: int, 
                 resource_id: int, details: Optional[str] = None):
    """Log an operation for audit purposes"""
    log_data = {
        "operation": operation,
        "user_id": user_id,
        "resource_id": resource_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    logger.info(f"Operation: {operation} | User: {user_id} | Resource: {resource_id} | Details: {details}")

def log_security_event(logger: logging.Logger, event: str, user_id: Optional[int] = None, 
                      details: Optional[Dict[str, Any]] = None):
    """Log security-related events"""
    log_data = {
        "event": event,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    logger.warning(f"Security Event: {event} | User: {user_id} | Details: {details}")

# Initialize logging when module is imported
setup_logging()
