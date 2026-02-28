from typing import Any, Dict, Optional


class BankSyncException(Exception):
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConnectionNotFoundError(BankSyncException):
    def __init__(self, connection_id: int):
        super().__init__(
            f"Bank connection with ID {connection_id} not found",
            "CONNECTION_NOT_FOUND",
        )


class LinkedAccountNotFoundError(BankSyncException):
    def __init__(self, account_id: int):
        super().__init__(
            f"Linked account with ID {account_id} not found",
            "LINKED_ACCOUNT_NOT_FOUND",
        )


class SyncLogNotFoundError(BankSyncException):
    def __init__(self, sync_log_id: int):
        super().__init__(
            f"Sync log with ID {sync_log_id} not found",
            "SYNC_LOG_NOT_FOUND",
        )


class TokenValidationError(BankSyncException):
    def __init__(self, message: str = "Invalid Monobank token"):
        super().__init__(message, "TOKEN_VALIDATION_FAILED")


class MonobankApiError(BankSyncException):
    def __init__(self, message: str = "Monobank API error"):
        super().__init__(message, "MONOBANK_API_ERROR")


class RateLimitError(BankSyncException):
    def __init__(self, seconds_remaining: int):
        super().__init__(
            f"Rate limit exceeded. Please wait {seconds_remaining} seconds.",
            "RATE_LIMIT_EXCEEDED",
            {"seconds_remaining": seconds_remaining},
        )


class EncryptionError(BankSyncException):
    def __init__(self, message: str = "Token encryption/decryption failed"):
        super().__init__(message, "ENCRYPTION_ERROR")


class SyncInProgressError(BankSyncException):
    def __init__(self, connection_id: int):
        super().__init__(
            f"Sync already in progress for connection {connection_id}",
            "SYNC_IN_PROGRESS",
        )


class AccountNotLinkedError(BankSyncException):
    def __init__(self, account_id: int):
        super().__init__(
            f"Account {account_id} is not linked to a FinFlow account",
            "ACCOUNT_NOT_LINKED",
        )


class ExternalServiceError(BankSyncException):
    def __init__(self, service_name: str, message: str):
        super().__init__(
            f"External service error ({service_name}): {message}",
            "EXTERNAL_SERVICE_ERROR",
        )


class DatabaseError(BankSyncException):
    def __init__(self, message: str, operation: str = ""):
        super().__init__(
            f"Database error during {operation}: {message}" if operation else f"Database error: {message}",
            "DATABASE_ERROR",
        )
