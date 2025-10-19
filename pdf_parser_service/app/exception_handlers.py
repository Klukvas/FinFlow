from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions import (
    PDFParsingError,
    UnsupportedBankError,
    FileProcessingError,
    InvalidPDFError,
    ParsingTimeoutError,
    BankNotFoundError,
    ErrorCodes
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def custom_validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request data",
            "errorCode": ErrorCodes.VALIDATION_ERROR
        }
    )

async def pdf_parsing_error_handler(request: Request, exc: PDFParsingError):
    """Handle PDF parsing errors"""
    logger.error(f"PDF parsing error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )

async def unsupported_bank_handler(request: Request, exc: UnsupportedBankError):
    """Handle unsupported bank errors"""
    logger.warning(f"Unsupported bank: {exc.bank_type}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )

async def file_processing_error_handler(request: Request, exc: FileProcessingError):
    """Handle file processing errors"""
    logger.error(f"File processing error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )

async def bank_not_found_handler(request: Request, exc: BankNotFoundError):
    """Handle bank not found errors"""
    logger.warning(f"Bank not found: {exc.bank_name}")
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "errorCode": exc.error_code
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "errorCode": ErrorCodes.INTERNAL_SERVER_ERROR
        }
    )
