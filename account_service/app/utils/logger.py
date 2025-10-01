import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def log_security_event(
    logger: logging.Logger, 
    event: str, 
    user_id: Optional[int] = None, 
    details: Optional[str] = None
) -> None:
    """Log security-related events"""
    log_data = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "details": details
    }
    logger.warning(f"SECURITY: {json.dumps(log_data)}")

def log_operation(
    logger: logging.Logger,
    operation: str,
    user_id: int,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log business operations"""
    log_data = {
        "operation": operation,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details
    }
    logger.info(f"OPERATION: {json.dumps(log_data)}")

def log_external_service_call(
    logger: logging.Logger,
    service: str,
    endpoint: str,
    status_code: int,
    duration: float
) -> None:
    """Log external service calls"""
    log_data = {
        "service": service,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(f"EXTERNAL_CALL: {json.dumps(log_data)}")
