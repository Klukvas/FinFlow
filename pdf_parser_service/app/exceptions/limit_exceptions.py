"""
Custom exceptions for PDF upload and record limit violations.

These exceptions are raised when users exceed their subscription plan limits.
"""


class PDFUploadLimitExceededError(Exception):
    """
    Raised when user exceeds monthly PDF upload limit.

    Example:
        Basic plan user has uploaded 1 PDF this month (limit = 1).
        Attempting 2nd upload raises this exception.

    HTTP Status: 429 Too Many Requests
    """

    def __init__(self, current_count: int, limit: int):
        self.current_count = current_count
        self.limit = limit
        super().__init__(
            f"Monthly PDF upload limit exceeded. Used {current_count}/{limit} uploads this month."
        )


class PDFRecordsLimitExceededError(Exception):
    """
    Raised when PDF contains more records than plan allows per upload.

    Example:
        Basic plan allows max 20 records per upload.
        Uploading PDF with 25 records raises this exception.

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, record_count: int, limit: int):
        self.record_count = record_count
        self.limit = limit
        super().__init__(
            f"PDF contains {record_count} records but your plan allows maximum {limit} records per upload."
        )
