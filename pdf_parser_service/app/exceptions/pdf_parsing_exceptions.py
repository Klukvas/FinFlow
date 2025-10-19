from fastapi import HTTPException
from typing import Optional

# Error codes constants
class ErrorCodes:
    # File processing errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    INVALID_PDF_FORMAT = "INVALID_PDF_FORMAT"
    FILE_PROCESSING_FAILED = "FILE_PROCESSING_FAILED"
    
    # PDF parsing errors
    PDF_PARSING_FAILED = "PDF_PARSING_FAILED"
    PDF_PARSING_TIMEOUT = "PDF_PARSING_TIMEOUT"
    NO_TRANSACTIONS_FOUND = "NO_TRANSACTIONS_FOUND"
    TRANSACTION_PARSING_FAILED = "TRANSACTION_PARSING_FAILED"
    
    # Bank support errors
    UNSUPPORTED_BANK_TYPE = "UNSUPPORTED_BANK_TYPE"
    BANK_NOT_FOUND = "BANK_NOT_FOUND"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_REQUEST_DATA = "INVALID_REQUEST_DATA"
    
    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class PDFParsingError(Exception):
    """Base exception for PDF parsing errors"""
    def __init__(self, message: str, error_code: str, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class UnsupportedBankError(PDFParsingError):
    """Exception raised when bank type is not supported"""
    def __init__(self, bank_type: str, supported_banks: list):
        self.bank_type = bank_type
        self.supported_banks = supported_banks
        message = f"Bank type '{bank_type}' is not supported. Supported banks: {', '.join(supported_banks)}"
        super().__init__(message, ErrorCodes.UNSUPPORTED_BANK_TYPE, {"bank_type": bank_type, "supported_banks": supported_banks})

class FileProcessingError(PDFParsingError):
    """Exception raised when file processing fails"""
    def __init__(self, message: str, error_code: str = ErrorCodes.FILE_PROCESSING_FAILED, file_name: Optional[str] = None):
        self.file_name = file_name
        super().__init__(message, error_code, {"file_name": file_name})

class InvalidPDFError(FileProcessingError):
    """Exception raised when PDF file is invalid or corrupted"""
    def __init__(self, file_name: Optional[str] = None):
        message = f"Invalid or corrupted PDF file{f' ({file_name})' if file_name else ''}"
        super().__init__(message, ErrorCodes.INVALID_PDF_FORMAT, file_name)

class ParsingTimeoutError(PDFParsingError):
    """Exception raised when PDF parsing times out"""
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        message = f"PDF parsing timed out after {timeout_seconds} seconds"
        super().__init__(message, ErrorCodes.PDF_PARSING_TIMEOUT, {"timeout_seconds": timeout_seconds})

class BankNotFoundError(PDFParsingError):
    """Exception raised when a specific bank is not found"""
    def __init__(self, bank_name: str):
        self.bank_name = bank_name
        message = f"Bank '{bank_name}' is not supported"
        super().__init__(message, ErrorCodes.BANK_NOT_FOUND, {"bank_name": bank_name})
