import os
import asyncio
from typing import Optional
from app.models.transaction import (
    ParsedTransaction, 
    BankType, 
    TransactionType,
    PDFParseResponse
)
from app.exceptions import (
    PDFParsingError,
    UnsupportedBankError,
    FileProcessingError,
    InvalidPDFError,
    ParsingTimeoutError
)
from app.utils.logger import get_logger
from app.services.parsers import MonobankParser

logger = get_logger(__name__)

class PDFParserService:
    """Service for parsing bank PDFs and extracting transaction data"""
    
    def __init__(self):
        self.monobank_parser = MonobankParser()
    
    async def parse_pdf(self, file_path: str, bank_type: Optional[BankType] = None) -> PDFParseResponse:
        """Parse PDF file and extract transactions (Monobank only)"""
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileProcessingError(f"File not found: {file_path}")
            
            # Only support Monobank for now
            if bank_type and bank_type != BankType.MONOBANK:
                raise UnsupportedBankError(bank_type.value, ["monobank"])
            
            # Parse PDF with timeout
            try:
                transactions = await asyncio.wait_for(
                    self.monobank_parser.parse_pdf(file_path),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                raise ParsingTimeoutError(30)
            
            return PDFParseResponse(
                transactions=transactions,
                bank_detected=BankType.MONOBANK,
                total_transactions=len(transactions),
                successful_parses=len(transactions),
                failed_parses=0,
                parsing_metadata={
                    "file_size": os.path.getsize(file_path),
                    "parsing_method": "monobank_parser",
                    "confidence_threshold": 0.7
                }
            )
            
        except Exception as e:
            if isinstance(e, (PDFParsingError, UnsupportedBankError, FileProcessingError, ParsingTimeoutError)):
                raise
            logger.error(f"Unexpected error parsing PDF: {e}")
            raise PDFParsingError(f"Failed to parse PDF: {str(e)}")