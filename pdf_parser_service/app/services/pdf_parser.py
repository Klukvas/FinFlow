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
    ParsingTimeoutError,
    ErrorCodes
)
from app.utils.logger import get_logger
from app.services.parsers import MonobankParser, PrivatbankParser, UkrsibBankParser, ABankParser, DeelParser

logger = get_logger(__name__)

class PDFParserService:
    """Service for parsing bank statements and extracting transaction data"""

    SUPPORTED_BANKS = ["monobank", "privatbank", "ukrsibbank", "abank", "deel"]

    def __init__(self):
        self.monobank_parser = MonobankParser()
        self.privatbank_parser = PrivatbankParser()
        self.ukrsib_parser = UkrsibBankParser()
        self.abank_parser = ABankParser()
        self.deel_parser = DeelParser()

    async def cleanup(self):
        """Cleanup resources (close HTTP clients, etc.)"""
        if hasattr(self.monobank_parser, 'category_client'):
            await self.monobank_parser.category_client.close()
            logger.info("Closed category service HTTP client")

    async def parse_pdf(self, file_path: str, bank_type: Optional[BankType] = None, language: str = "en", user_id: int = None) -> PDFParseResponse:
        """Parse bank statement file and extract transactions"""
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileProcessingError(f"File not found: {file_path}", ErrorCodes.FILE_NOT_FOUND)

            # Route to the correct parser
            if bank_type == BankType.PRIVATBANK:
                return await self._parse_privatbank(file_path, language, user_id)

            if bank_type == BankType.UKRSIBBANK:
                return await self._parse_ukrsibbank(file_path, language, user_id)

            if bank_type == BankType.ABANK:
                return await self._parse_abank(file_path, language, user_id)

            if bank_type == BankType.DEEL:
                return await self._parse_deel(file_path, language, user_id)

            if bank_type is None or bank_type == BankType.MONOBANK:
                return await self._parse_monobank(file_path, bank_type, language, user_id)

            raise UnsupportedBankError(bank_type.value, self.SUPPORTED_BANKS)

        except Exception as e:
            if isinstance(e, (PDFParsingError, UnsupportedBankError, FileProcessingError, ParsingTimeoutError)):
                raise
            logger.error(f"Unexpected error parsing file: {e}")
            raise PDFParsingError(f"Failed to parse file: {str(e)}", ErrorCodes.PDF_PARSING_FAILED)

    async def _parse_monobank(self, file_path: str, bank_type: Optional[BankType], language: str, user_id: int) -> PDFParseResponse:
        """Parse Monobank PDF statement"""
        try:
            transactions = await asyncio.wait_for(
                self.monobank_parser.parse_pdf(file_path, language, user_id),
                timeout=30.0
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

    async def _parse_privatbank(self, file_path: str, language: str, user_id: int) -> PDFParseResponse:
        """Parse PrivatBank XLSX statement"""
        try:
            transactions = await asyncio.wait_for(
                self.privatbank_parser.parse_pdf(file_path, language, user_id),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ParsingTimeoutError(30)

        return PDFParseResponse(
            transactions=transactions,
            bank_detected=BankType.PRIVATBANK,
            total_transactions=len(transactions),
            successful_parses=len(transactions),
            failed_parses=0,
            parsing_metadata={
                "file_size": os.path.getsize(file_path),
                "parsing_method": "privatbank_parser",
                "confidence_threshold": 0.7
            }
        )

    async def _parse_ukrsibbank(self, file_path: str, language: str, user_id: int) -> PDFParseResponse:
        """Parse UKRSIBBANK PDF statement"""
        try:
            transactions = await asyncio.wait_for(
                self.ukrsib_parser.parse_pdf(file_path, language, user_id),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ParsingTimeoutError(30)

        return PDFParseResponse(
            transactions=transactions,
            bank_detected=BankType.UKRSIBBANK,
            total_transactions=len(transactions),
            successful_parses=len(transactions),
            failed_parses=0,
            parsing_metadata={
                "file_size": os.path.getsize(file_path),
                "parsing_method": "ukrsibbank_parser",
                "confidence_threshold": 0.7
            }
        )

    async def _parse_abank(self, file_path: str, language: str, user_id: int) -> PDFParseResponse:
        """Parse A-Bank PDF statement"""
        try:
            transactions = await asyncio.wait_for(
                self.abank_parser.parse_pdf(file_path, language, user_id),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ParsingTimeoutError(30)

        return PDFParseResponse(
            transactions=transactions,
            bank_detected=BankType.ABANK,
            total_transactions=len(transactions),
            successful_parses=len(transactions),
            failed_parses=0,
            parsing_metadata={
                "file_size": os.path.getsize(file_path),
                "parsing_method": "abank_parser",
                "confidence_threshold": 0.7
            }
        )

    async def _parse_deel(self, file_path: str, language: str, user_id: int) -> PDFParseResponse:
        """Parse Deel CSV statement"""
        try:
            transactions = await asyncio.wait_for(
                self.deel_parser.parse_pdf(file_path, language, user_id),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ParsingTimeoutError(30)

        return PDFParseResponse(
            transactions=transactions,
            bank_detected=BankType.DEEL,
            total_transactions=len(transactions),
            successful_parses=len(transactions),
            failed_parses=0,
            parsing_metadata={
                "file_size": os.path.getsize(file_path),
                "parsing_method": "deel_parser",
                "confidence_threshold": 0.7
            }
        )
