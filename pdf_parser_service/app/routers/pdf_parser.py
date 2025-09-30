from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import Optional
import os
import uuid
from app.models.transaction import (
    PDFParseResponse,
)
from app.services.pdf_parser import PDFParserService
from app.config import settings
from app.utils.logger import get_logger
from app.config.bank_headers import BANK_HEADERS 
from app.dependencies import get_current_user_id
logger = get_logger(__name__)
router = APIRouter(prefix="/pdf", tags=["pdf-parser"])

# Initialize services
pdf_parser_service = PDFParserService()

@router.post("/parse", response_model=PDFParseResponse)
async def parse_pdf(
    file: UploadFile = File(..., description="PDF file to parse"),
    bank_type: Optional[str] = Form(None, description="Specific bank type (optional)"),
    user_id: int = Depends(get_current_user_id)
):
    """
    Parse a bank PDF file and extract transaction data
    """
    try:
        logger.info(f"Received file upload request: {file.filename}, size: {file.size}, type: {file.content_type}")
        
        # Validate file type
        if file.content_type != "application/pdf":
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_directory, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        temp_file_path = os.path.join(settings.upload_directory, f"{file_id}{file_extension}")
        
        try:
            # Save uploaded file temporarily
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"Processing PDF file: {file.filename} (ID: {file_id})")
            
            # Parse PDF
            from app.models.transaction import BankType
            bank_type_enum = BankType(bank_type) if bank_type else None
            
            result = await pdf_parser_service.parse_pdf(temp_file_path, bank_type_enum)
            
            logger.info(f"Successfully parsed PDF: {len(result.transactions)} transactions found")
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}")
        if isinstance(e, HTTPException):
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
        raise HTTPException(
            status_code=404,
            detail=f"Bank '{bank_name}' is not supported"
        )
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
