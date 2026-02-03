"""
PDF Upload model for tracking upload history and enforcing limits.

This model stores metadata about each PDF upload attempt to enable:
- Monthly upload count limits (e.g., Basic plan: 1 upload/month)
- Upload history and analytics
- Audit trail for debugging
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class PDFUpload(Base):
    """
    Tracks PDF upload attempts for usage limit enforcement.

    The composite index on (user_id, created_at) enables efficient
    monthly limit queries using the same pattern as expense/income services.

    Monthly limit query pattern:
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = db.query(PDFUpload).filter(
            PDFUpload.user_id == user_id,
            PDFUpload.created_at >= current_month_start
        ).count()
    """
    __tablename__ = "pdf_uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Upload metadata
    filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes

    # Parsed results
    total_transactions = Column(Integer, nullable=False, default=0)
    successful_parses = Column(Integer, nullable=False, default=0)
    failed_parses = Column(Integer, nullable=False, default=0)

    # Status: 'success', 'failed', 'partial'
    status = Column(String(16), nullable=False, default='success')

    # Timestamps for monthly counting (follows expense/income pattern)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # CRITICAL: Composite index for monthly limit queries
    # This index enables fast filtering: WHERE user_id = X AND created_at >= month_start
    __table_args__ = (
        Index('idx_pdf_uploads_user_created', 'user_id', 'created_at'),
    )
