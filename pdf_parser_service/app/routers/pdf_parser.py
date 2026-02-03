from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import Optional
from sqlalchemy.orm import Session
import os
import uuid
from app.models.transaction import (
    PDFParseResponse,
    PDFLimitInfo,
)
from app.services.pdf_parser import PDFParserService
from app.config import settings
from app.utils.logger import get_logger
from app.config.bank_headers import BANK_HEADERS
from app.dependencies import get_current_user_id
from app.database import get_db
from app.repositories.pdf_upload_repository import PDFUploadRepository
from app.clients.subscription_client import SubscriptionClient
from app.exceptions import (
    FileProcessingError,
    BankNotFoundError,
    ErrorCodes
)
from app.exceptions.limit_exceptions import (
    PDFUploadLimitExceededError,
    PDFRecordsLimitExceededError
)
logger = get_logger(__name__)
router = APIRouter(prefix="/pdf", tags=["pdf-parser"])

# Initialize services
pdf_parser_service = PDFParserService()
subscription_client = SubscriptionClient()

@router.post("/parse", response_model=PDFParseResponse)
async def parse_pdf(
    file: UploadFile = File(..., description="PDF file to parse"),
    bank_type: Optional[str] = Form(None, description="Specific bank type (optional)"),
    language: str = Form("en", description="Language for MCC category translations (ru, uk, en)"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Parse a bank PDF file and extract transaction data with subscription-based usage limits.

    - **file**: PDF file to parse
    - **bank_type**: Specific bank type (optional, defaults to auto-detection)
    - **language**: Language for MCC category translations (ru, uk, en, defaults to en)

    Limits enforced:
    1. Monthly upload quota (pdf_uploads_per_month)
    2. Records per upload (pdf_records_per_upload)

    Returns parsed transaction data with limit information.
    """
    temp_file_path = None
    upload_repo = PDFUploadRepository(db)

    try:
        # Validate language parameter
        allowed_languages = ["en", "ru", "uk"]
        if language not in allowed_languages:
            raise FileProcessingError(
                f"Invalid language. Allowed values: {', '.join(allowed_languages)}",
                ErrorCodes.VALIDATION_ERROR
            )

        # STAGE 1: Check monthly upload limit BEFORE processing
        monthly_count = upload_repo.get_monthly_upload_count(user_id)
        if not subscription_client.check_pdf_upload_limit(user_id, monthly_count):
            features = subscription_client.get_user_features(user_id)
            limit = features.get("pdf_uploads_per_month", {}).get("limit_value", 0)
            raise PDFUploadLimitExceededError(monthly_count, limit)

        # Validate file size (handle None case)
        if file.size is None:
            logger.warning("File size is None, reading file to check size")
            # Read file to check actual size
            content = await file.read()
            actual_size = len(content)
            await file.seek(0)  # Reset file pointer
            
            if actual_size > settings.max_file_size:
                raise FileProcessingError(
                    f"File size exceeds maximum allowed size of {settings.max_file_size} bytes",
                    ErrorCodes.FILE_SIZE_EXCEEDED
                )
        elif file.size > settings.max_file_size:
            raise FileProcessingError(
                f"File size exceeds maximum allowed size of {settings.max_file_size} bytes",
                ErrorCodes.FILE_SIZE_EXCEEDED
            )
        
        logger.info(f"Received file upload request: {file.filename}, size: {file.size}, type: {file.content_type}")
        
        # Validate file type (MIME type check)
        if file.content_type != "application/pdf":
            logger.warning(f"Invalid file type: {file.content_type}")
            raise FileProcessingError(
                "Only PDF files are supported",
                ErrorCodes.INVALID_FILE_TYPE
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_directory, exist_ok=True)
        
        # Generate unique filename with sanitized extension
        file_id = str(uuid.uuid4())
        # Sanitize filename - only allow .pdf extension, prevent path traversal
        if file.filename:
            original_extension = os.path.splitext(file.filename)[1].lower()
            # Only allow .pdf extension
            if original_extension != ".pdf":
                file_extension = ".pdf"
            else:
                file_extension = ".pdf"
        else:
            file_extension = ".pdf"
        
        # Use only the UUID and extension, no user input in path
        temp_file_path = os.path.join(settings.upload_directory, f"{file_id}{file_extension}")
        
        # Ensure the path is within upload directory (prevent path traversal)
        real_upload_dir = os.path.realpath(settings.upload_directory)
        real_temp_path = os.path.realpath(temp_file_path)
        if not real_temp_path.startswith(real_upload_dir):
            raise FileProcessingError(
                "Invalid file path",
                ErrorCodes.FILE_PROCESSING_FAILED
            )
        
        try:
            # Save uploaded file temporarily
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Validate actual PDF content (magic bytes)
            with open(temp_file_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    raise FileProcessingError(
                        "File is not a valid PDF (invalid header)",
                        ErrorCodes.INVALID_PDF_FORMAT
                    )
            
            logger.info(f"Processing PDF file: {file.filename} (ID: {file_id})")
            
            # Parse PDF
            from app.models.transaction import BankType
            bank_type_enum = BankType(bank_type) if bank_type else None
            
            result = await pdf_parser_service.parse_pdf(temp_file_path, bank_type_enum, language, user_id)

            # STAGE 2: Check records per upload limit AFTER parsing
            if not subscription_client.check_pdf_records_limit(user_id, result.total_transactions):
                features = subscription_client.get_user_features(user_id)
                limit = features.get("pdf_records_per_upload", {}).get("limit_value", 0)
                raise PDFRecordsLimitExceededError(result.total_transactions, limit)

            # Log successful upload for monthly tracking
            upload_repo.create_upload_record(
                user_id=user_id,
                filename=file.filename,
                file_size=file.size,
                total_transactions=result.total_transactions,
                successful_parses=result.successful_parses,
                failed_parses=result.failed_parses,
                status='success'
            )

            # Add limit info to response
            features = subscription_client.get_user_features(user_id)
            new_monthly_count = monthly_count + 1

            result.limit_info = PDFLimitInfo(
                uploads_per_month=features.get("pdf_uploads_per_month", {}).get("limit_value"),
                records_per_upload=features.get("pdf_records_per_upload", {}).get("limit_value"),
                uploads_used_this_month=new_monthly_count,
                uploads_remaining=(
                    features.get("pdf_uploads_per_month", {}).get("limit_value") - new_monthly_count
                    if features.get("pdf_uploads_per_month", {}).get("limit_value") is not None
                    else None
                ),
                plan_code=features.get("pdf_uploads_per_month", {}).get("plan_code", "unknown")
            )

            logger.info(
                f"Successfully parsed PDF: {len(result.transactions)} transactions found, "
                f"uploads used: {new_monthly_count}/{features.get('pdf_uploads_per_month', {}).get('limit_value')}"
            )

            return result
            
        finally:
            # Clean up temporary file with better error handling
            if temp_file_path:
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except PermissionError:
                    logger.error(f"Permission denied when deleting temporary file: {temp_file_path}")
                except OSError as e:
                    logger.error(f"OS error when deleting temporary file: {temp_file_path}, error: {e}")
    
    except PDFUploadLimitExceededError as e:
        # Record failed attempt due to monthly upload limit
        upload_repo.create_upload_record(
            user_id=user_id,
            filename=file.filename,
            file_size=file.size if file.size else 0,
            status='failed',
            total_transactions=0
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": str(e),
                "error_code": "PDF_UPLOAD_LIMIT_EXCEEDED",
                "current_count": e.current_count,
                "limit": e.limit,
                "message": f"You have used {e.current_count}/{e.limit} PDF uploads this month. Please upgrade your plan or wait until next month."
            }
        )

    except PDFRecordsLimitExceededError as e:
        # Record failed attempt due to record count limit
        upload_repo.create_upload_record(
            user_id=user_id,
            filename=file.filename,
            file_size=file.size if file.size else 0,
            status='failed',
            total_transactions=e.record_count
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "error_code": "PDF_RECORDS_LIMIT_EXCEEDED",
                "record_count": e.record_count,
                "limit": e.limit,
                "message": f"This PDF contains {e.record_count} records but your plan allows maximum {e.limit} records per upload. Please upgrade your plan or split the PDF."
            }
        )

    except Exception as e:
        # Clean up on exception as well
        if temp_file_path:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up temporary file on exception: {cleanup_error}")

        logger.error(f"Error processing PDF upload: {e}")
        if isinstance(e, (FileProcessingError, BankNotFoundError)):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/supported-banks")
async def get_supported_banks(
    user_id: int = Depends(get_current_user_id)
):
    """
    Get list of supported bank types
    """
    return {
        "supported_banks": list([bank.lower() for bank in BANK_HEADERS.keys()]),
        "total_count": len(BANK_HEADERS)
    }

@router.get("/languages/{bank_name}")
async def get_available_languages(bank_name: str, user_id: int = Depends(get_current_user_id)):
    """
    Get available languages for a specific bank
    """
    
    # Normalize bank name
    bank_name_upper = bank_name.upper()
    
    
    # Check if bank is supported
    if bank_name_upper not in [bank.upper() for bank in BANK_HEADERS.keys()]:
        raise BankNotFoundError(bank_name)
    available_languages = list(BANK_HEADERS.get(bank_name_upper, {}).keys())
    
    return {
        "bank": bank_name_upper,
        "available_languages": available_languages,
        "total_languages": len(available_languages)
    }

@router.get("/health")
async def health_check():
    """
    Health check for PDF parser service
    """
    return {
        "status": "healthy",
        "service": "pdf-parser",
        "supported_banks": len(BANK_HEADERS.keys())
    }
