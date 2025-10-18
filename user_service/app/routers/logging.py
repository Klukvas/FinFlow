"""
Frontend Logging API Router

This router handles frontend log collection and forwarding to the centralized logging system.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.exceptions.user_errors import UserValidationError, UserErrorCode
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sys
import os

# Add logging utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logging'))

from logging_utils import get_structured_logger, set_request_context, generate_request_id

router = APIRouter(prefix="/api/logging", tags=["Frontend Logging"])

# Initialize logger
logger = get_structured_logger(__name__, "user_service")

class FrontendLogEntry(BaseModel):
    """Single frontend log entry"""
    level: str
    message: str
    timestamp: Optional[str] = None
    source: Optional[str] = None  # file, line, function
    stack: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class FrontendLogBatch(BaseModel):
    """Batch of frontend log entries"""
    logs: List[FrontendLogEntry]
    session_id: Optional[str] = None
    user_id: Optional[int] = None

class LogResponse(BaseModel):
    """Response for log submission"""
    success: bool
    processed: int
    message: str

@router.post(
    "/frontend",
    response_model=LogResponse,
    status_code=200,
    summary="Submit frontend logs",
    description="Submit frontend application logs for centralized collection",
    responses={
        200: {"description": "Logs processed successfully"},
        400: {"description": "Invalid log data"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def submit_frontend_logs(
    log_batch: FrontendLogBatch,
    request: Request
):
    """
    Submit frontend logs to the centralized logging system.
    
    This endpoint accepts batches of frontend log entries and forwards them
    to the structured logging system for processing and storage.
    """
    try:
        # Set request context
        request_id = generate_request_id()
        set_request_context(request_id, log_batch.user_id, "user_service")
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        processed_count = 0
        
        for log_entry in log_batch.logs:
            try:
                # Map frontend log level to backend level
                level_mapping = {
                    "log": "info",
                    "info": "info", 
                    "warn": "warning",
                    "warning": "warning",
                    "error": "error",
                    "debug": "debug"
                }
                
                backend_level = level_mapping.get(log_entry.level.lower(), "info")
                
                # Prepare log message
                message = f"Frontend {log_entry.level.upper()}: {log_entry.message}"
                
                # Prepare extra fields
                extra_fields = {
                    "category": "frontend",
                    "operation": "frontend_log",
                    "source": log_entry.source,
                    "session_id": log_entry.session_id or log_batch.session_id,
                    "url": log_entry.url,
                    "user_agent": log_entry.user_agent or user_agent,
                    "ip_address": client_ip,
                    "frontend_timestamp": log_entry.timestamp,
                }
                
                # Add stack trace if available
                if log_entry.stack:
                    extra_fields["stack_trace"] = log_entry.stack
                
                # Add extra data if provided
                if log_entry.extra:
                    extra_fields.update(log_entry.extra)
                
                # Log the entry
                getattr(logger, backend_level)(
                    message,
                    **extra_fields
                )
                
                processed_count += 1
                
            except Exception as e:
                # Log the error but continue processing other logs
                logger.error(
                    f"Failed to process frontend log entry: {str(e)}",
                    category="frontend",
                    operation="log_processing_error",
                    user_id=log_batch.user_id
                )
        
        # Log the batch submission
        logger.info(
            f"Processed {processed_count} frontend log entries",
            category="frontend",
            operation="log_batch_processed",
            user_id=log_batch.user_id,
            session_id=log_batch.session_id,
            processed_count=processed_count
        )
        
        return LogResponse(
            success=True,
            processed=processed_count,
            message=f"Successfully processed {processed_count} log entries"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to process frontend log batch: {str(e)}",
            category="frontend",
            operation="log_batch_error",
            user_id=log_batch.user_id
        )
        
        raise UserValidationError("Failed to process log batch")

@router.post(
    "/frontend/error",
    response_model=LogResponse,
    status_code=200,
    summary="Submit frontend error",
    description="Submit a single frontend error for immediate attention",
    responses={
        200: {"description": "Error logged successfully"},
        400: {"description": "Invalid error data"}
    }
)
async def submit_frontend_error(
    error_log: FrontendLogEntry,
    request: Request
):
    """
    Submit a single frontend error for immediate logging and alerting.
    
    This endpoint is optimized for error reporting and may trigger
    immediate alerts or notifications.
    """
    try:
        # Set request context
        request_id = generate_request_id()
        set_request_context(request_id, error_log.user_id, "user_service")
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Prepare error message
        message = f"Frontend ERROR: {error_log.message}"
        
        # Prepare extra fields
        extra_fields = {
            "category": "frontend_error",
            "operation": "frontend_error_report",
            "source": error_log.source,
            "session_id": error_log.session_id,
            "url": error_log.url,
            "user_agent": error_log.user_agent or user_agent,
            "ip_address": client_ip,
            "frontend_timestamp": error_log.timestamp,
            "priority": "high"  # Mark as high priority for errors
        }
        
        # Add stack trace if available
        if error_log.stack:
            extra_fields["stack_trace"] = error_log.stack
        
        # Add extra data if provided
        if error_log.extra:
            extra_fields.update(error_log.extra)
        
        # Log the error
        logger.error(message, **extra_fields)
        
        return LogResponse(
            success=True,
            processed=1,
            message="Error logged successfully"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to process frontend error: {str(e)}",
            category="frontend",
            operation="error_processing_failed"
        )
        
        raise UserValidationError("Failed to process error log")

@router.get(
    "/health",
    summary="Logging service health check",
    description="Check if the logging service is healthy and accepting logs"
)
async def logging_health_check():
    """Health check endpoint for the logging service"""
    try:
        # Test logging functionality
        logger.info(
            "Logging service health check",
            category="health",
            operation="health_check"
        )
        
        return {
            "status": "healthy",
            "service": "frontend_logging",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(
            f"Logging service health check failed: {str(e)}",
            category="health",
            operation="health_check_failed"
        )
        
        raise UserValidationError("Logging service unhealthy")
