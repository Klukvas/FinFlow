from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Integer,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from ..database import Base


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class JobExecution(Base):
    """Track job execution history for observability and debugging"""
    
    __tablename__ = "job_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String(128), nullable=False, index=True)
    
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Execution details
    items_processed = Column(Integer, default=0)
    items_succeeded = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Additional context
    extra_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RenewalAttempt(Base):
    """Track individual subscription renewal attempts"""
    
    __tablename__ = "renewal_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_execution_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    subscription_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(128), nullable=False)
    
    # Payment details
    payment_id = Column(UUID(as_uuid=True), nullable=True)
    amount = Column(String(32), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # Result
    status = Column(String(32), nullable=False)  # SUCCESS, FAILED, SKIPPED
    failure_reason = Column(Text, nullable=True)
    
    # Retry tracking
    attempt_number = Column(Integer, default=1)
    
    extra_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
