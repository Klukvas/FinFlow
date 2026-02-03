"""
PDF Upload Repository for database operations.

This repository handles all database operations for PDF upload tracking,
including monthly upload count queries for limit enforcement.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.models.pdf_upload import PDFUpload


class PDFUploadRepository:
    """Repository for PDFUpload database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_monthly_upload_count(self, user_id: int) -> int:
        """
        Count PDF uploads for current calendar month (UTC).

        Uses the same pattern as expense/income monthly limits:
        - UTC calendar month (not rolling 30 days)
        - Based on created_at timestamp
        - Uses composite index (user_id, created_at) for performance

        Args:
            user_id: User ID to count uploads for

        Returns:
            Number of uploads in current month
        """
        current_month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        count = self.db.query(PDFUpload).filter(
            PDFUpload.user_id == user_id,
            PDFUpload.created_at >= current_month_start
        ).count()

        return count

    def create_upload_record(
        self,
        user_id: int,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        total_transactions: int = 0,
        successful_parses: int = 0,
        failed_parses: int = 0,
        status: str = 'success'
    ) -> PDFUpload:
        """
        Create a new PDF upload record.

        This is called after PDF parsing to log the upload attempt,
        enabling monthly limit tracking and upload history.

        Args:
            user_id: User ID
            filename: Original PDF filename
            file_size: File size in bytes
            total_transactions: Total transactions found in PDF
            successful_parses: Successfully parsed transactions
            failed_parses: Failed parse attempts
            status: Upload status ('success', 'failed', 'partial')

        Returns:
            Created PDFUpload instance
        """
        upload = PDFUpload(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            total_transactions=total_transactions,
            successful_parses=successful_parses,
            failed_parses=failed_parses,
            status=status
        )

        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)

        return upload

    def get_upload_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[PDFUpload]:
        """
        Get upload history for a user (for future features/analytics).

        Args:
            user_id: User ID
            limit: Max records to return
            offset: Offset for pagination

        Returns:
            List of PDFUpload records, newest first
        """
        return (
            self.db.query(PDFUpload)
            .filter(PDFUpload.user_id == user_id)
            .order_by(PDFUpload.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
