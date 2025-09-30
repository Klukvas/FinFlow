from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions import (
    PDFParsingError,
    UnsupportedBankError,
    FileProcessingError,
    InvalidPDFError,
    ParsingTimeoutError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors() if hasattr(exc, 'errors') else str(exc)
        }
    )

async def pdf_parsing_error_handler(request: Request, exc: PDFParsingError):
    """Handle PDF parsing errors"""
    logger.error(f"PDF parsing error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=400,
        content={
            "error": "PDF Parsing Error",
            "message": exc.message,
            "details": exc.details
        }
    )

async def unsupported_bank_handler(request: Request, exc: UnsupportedBankError):
    """Handle unsupported bank errors"""
    logger.warning(f"Unsupported bank: {exc.bank_type}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Unsupported Bank",
            "message": exc.message,
            "supported_banks": exc.supported_banks
        }
    )

async def file_processing_error_handler(request: Request, exc: FileProcessingError):
    """Handle file processing errors"""
    logger.error(f"File processing error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "File Processing Error",
            "message": exc.message,
            "file_name": exc.file_name
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail
        }
    )
