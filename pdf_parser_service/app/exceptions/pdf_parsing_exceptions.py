from fastapi import HTTPException
from typing import Optional

class PDFParsingError(Exception):
    """Base exception for PDF parsing errors"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class UnsupportedBankError(PDFParsingError):
    """Exception raised when bank type is not supported"""
    def __init__(self, bank_type: str, supported_banks: list):
        self.bank_type = bank_type
        self.supported_banks = supported_banks
        message = f"Bank type '{bank_type}' is not supported. Supported banks: {', '.join(supported_banks)}"
        super().__init__(message, {"bank_type": bank_type, "supported_banks": supported_banks})

class FileProcessingError(PDFParsingError):
    """Exception raised when file processing fails"""
    def __init__(self, message: str, file_name: Optional[str] = None):
        self.file_name = file_name
        super().__init__(message, {"file_name": file_name})

class InvalidPDFError(FileProcessingError):
    """Exception raised when PDF file is invalid or corrupted"""
    def __init__(self, file_name: Optional[str] = None):
        message = f"Invalid or corrupted PDF file{f' ({file_name})' if file_name else ''}"
        super().__init__(message, file_name)

class ParsingTimeoutError(PDFParsingError):
    """Exception raised when PDF parsing times out"""
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        message = f"PDF parsing timed out after {timeout_seconds} seconds"
        super().__init__(message, {"timeout_seconds": timeout_seconds})
