"""
Enhanced JSON Logging Utilities for Accounting App

This module provides structured JSON logging capabilities for all microservices,
enabling better log aggregation, parsing, and monitoring with Loki/Promtail.
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from functools import wraps
import traceback

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)
service_name_var: ContextVar[Optional[str]] = ContextVar('service_name', default=None)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context variables if available
        if request_id_var.get():
            log_entry["request_id"] = request_id_var.get()
        
        if user_id_var.get():
            log_entry["user_id"] = user_id_var.get()
        
        # Add extra fields from the log record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)

class StructuredLogger:
    """Enhanced logger with structured logging capabilities"""
    
    def __init__(self, name: str, service_name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.service_name = service_name
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter(service_name))
        self.logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log with additional context"""
        extra_fields = {
            "category": kwargs.get("category", "general"),
            "operation": kwargs.get("operation"),
            "resource_id": kwargs.get("resource_id"),
            "duration_ms": kwargs.get("duration_ms"),
            "status_code": kwargs.get("status_code"),
            "ip_address": kwargs.get("ip_address"),
            "user_agent": kwargs.get("user_agent"),
            "endpoint": kwargs.get("endpoint"),
            "method": kwargs.get("method"),
        }
        
        # Remove None values
        extra_fields = {k: v for k, v in extra_fields.items() if v is not None}
        
        # Create log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name, getattr(logging, level.upper()), 
            "", 0, message, (), None
        )
        record.extra_fields = extra_fields
        
        # Log the record
        getattr(self.logger, level.lower())(message, extra={"extra_fields": extra_fields})
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self._log_with_context("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self._log_with_context("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self._log_with_context("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self._log_with_context("DEBUG", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self._log_with_context("CRITICAL", message, **kwargs)
    
    # Specialized logging methods
    def log_security_event(self, event: str, user_id: Optional[int] = None, 
                          details: Optional[str] = None, ip_address: Optional[str] = None):
        """Log security-related events"""
        self.warning(
            f"Security event: {event}",
            category="security",
            operation="security_event",
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    def log_business_operation(self, operation: str, user_id: int, 
                              resource_id: Optional[str] = None, 
                              details: Optional[str] = None):
        """Log business operations for audit trail"""
        self.info(
            f"Business operation: {operation}",
            category="business",
            operation=operation,
            user_id=user_id,
            resource_id=resource_id,
            details=details
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int,
                       duration_ms: Optional[float] = None, user_id: Optional[int] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                       request_id: Optional[str] = None):
        """Log API requests"""
        level = "info" if 200 <= status_code < 400 else "warning" if 400 <= status_code < 500 else "error"
        getattr(self, level)(
            f"API request: {method} {endpoint}",
            category="api",
            operation="api_request",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id
        )
    
    def log_external_service_call(self, service: str, endpoint: str, status_code: int,
                                 duration_ms: Optional[float] = None, error: Optional[str] = None):
        """Log external service calls"""
        level = "info" if 200 <= status_code < 400 else "error"
        message = f"External service call: {service} {endpoint}"
        if error:
            message += f" - Error: {error}"
        
        getattr(self, level)(
            message,
            category="external_service",
            operation="external_call",
            endpoint=f"{service}:{endpoint}",
            status_code=status_code,
            duration_ms=duration_ms
        )
    
    def log_database_operation(self, operation: str, table: str, duration_ms: Optional[float] = None,
                              user_id: Optional[int] = None, error: Optional[str] = None):
        """Log database operations"""
        level = "info" if not error else "error"
        message = f"Database operation: {operation} on {table}"
        if error:
            message += f" - Error: {error}"
        
        getattr(self, level)(
            message,
            category="database",
            operation=operation,
            resource_id=table,
            duration_ms=duration_ms,
            user_id=user_id
        )
    
    def log_authentication(self, email: str, success: bool, details: Optional[str] = None,
                          ip_address: Optional[str] = None):
        """Log authentication attempts"""
        status = "SUCCESS" if success else "FAILED"
        level = "info" if success else "warning"
        
        getattr(self, level)(
            f"Authentication {status}: {email}",
            category="authentication",
            operation="login_attempt",
            user_id=email,  # Using email as identifier
            details=details,
            ip_address=ip_address
        )

def get_structured_logger(name: str, service_name: str, level: str = "INFO") -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name, service_name, level)

def set_request_context(request_id: str, user_id: Optional[int] = None, service_name: Optional[str] = None):
    """Set request context for correlation"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if service_name:
        service_name_var.set(service_name)

def clear_request_context():
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)
    service_name_var.set(None)

def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())

def log_function_call(func):
    """Decorator to log function calls with timing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_structured_logger(func.__module__, service_name_var.get() or "unknown")
        start_time = datetime.utcnow()
        request_id = request_id_var.get() or generate_request_id()
        
        logger.debug(
            f"Function call: {func.__name__}",
            category="function",
            operation="function_call",
            request_id=request_id
        )
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.debug(
                f"Function completed: {func.__name__}",
                category="function",
                operation="function_complete",
                request_id=request_id,
                duration_ms=duration
            )
            
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                f"Function error: {func.__name__} - {str(e)}",
                category="function",
                operation="function_error",
                request_id=request_id,
                duration_ms=duration
            )
            raise
    
    return wrapper

# Convenience function for backward compatibility
def get_logger(name: str, service_name: str = None) -> StructuredLogger:
    """Get a logger instance (backward compatible)"""
    if service_name is None:
        service_name = name.split('.')[-1]  # Use last part of name as service
    return get_structured_logger(name, service_name)
