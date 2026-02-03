from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import pdfplumber
from app.models.transaction import ParsedTransaction, BankType, TransactionType
from app.config.bank_headers import get_headers_for_bank, get_patterns_for_bank
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BasePDFParser(ABC):
    """Abstract base class for PDF parsers"""
    
    def __init__(self, bank_type: BankType):
        self.bank_type = bank_type
        self.logger = get_logger(f"{__name__}.{bank_type.value}")
    
    @abstractmethod
    async def parse_pdf(self, file_path: str, language: str = "en", user_id: int = None) -> List[ParsedTransaction]:
        """Parse PDF file and extract transactions"""
        pass
    
    @abstractmethod
    async def _extract_transactions_from_table(self, table: List[List[str]], language: str = "en", user_id: int = None) -> List[ParsedTransaction]:
        """Extract transactions from a parsed table"""
        pass
    
    async def _extract_transactions_from_tables(self, tables: List[List[List[str]]], language: str = "en", user_id: int = None) -> List[ParsedTransaction]:
        """Extract transactions from multiple tables"""
        all_transactions = []
        
        for i, table in enumerate(tables):
            self.logger.info(f"Processing table {i + 1}/{len(tables)}")
            try:
                transactions = await self._extract_transactions_from_table(table, language, user_id)
                all_transactions.extend(transactions)
                self.logger.info(f"Extracted {len(transactions)} transactions from table {i + 1}")
            except Exception as e:
                self.logger.error(f"Error processing table {i + 1}: {e}")
                continue
        
        self.logger.info(f"Total transactions extracted: {len(all_transactions)}")
        return all_transactions
    
    def _parse_date(self, date_str: str, date_format: str = r'(\d{2}\.\d{2}\.\d{4})') -> Optional[date]:
        """Parse date string to date object"""
        try:
            if not date_str or not re.search(date_format, date_str):
                return None
                
            date_match = re.search(date_format, date_str)
            if not date_match:
                return None
                
            date_parts = date_match.group(1).split('.')
            if len(date_parts) != 3:
                return None
                
            return date(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            if not amount_str:
                return None
                
            # Clean amount string (remove spaces, handle negative values)
            cleaned_amount = amount_str.replace(' ', '').replace(',', '.')
            
            # Handle negative values
            is_negative = cleaned_amount.startswith('-')
            cleaned_amount = cleaned_amount.lstrip('-')
            
            amount = float(cleaned_amount)
            if amount <= 0:
                return None
                
            return -amount if is_negative else amount
        except (ValueError, InvalidOperation) as e:
            self.logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            return None
    
    def _determine_transaction_type(self, amount: float) -> TransactionType:
        """Determine if transaction is income or expense based on amount"""
        return TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
    
    def _calculate_confidence_score(self, description: str, transaction_date: date, amount: float) -> float:
        """Calculate confidence score for parsed transaction"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence based on data quality
        if len(description) > 5:
            confidence += 0.1
        if len(description) > 15:
            confidence += 0.1
        if transaction_date > date(2020, 1, 1):  # Reasonable date
            confidence += 0.1
        if abs(amount) > 0.01:  # Non-zero amount
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    def _extract_tables_from_pdf(self, file_path: str) -> List[List[List[str]]]:
        """Extract all tables from PDF file"""
        from app.exceptions import InvalidPDFError, FileProcessingError, ErrorCodes
        
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                # Check if PDF has any pages
                if not pdf.pages:
                    self.logger.error("PDF file has no pages")
                    raise InvalidPDFError(file_path)
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        page_tables = page.extract_tables()
                        if page_tables:
                            tables.extend(page_tables)
                    except Exception as page_error:
                        self.logger.warning(f"Failed to extract tables from page {page_num}: {page_error}")
                        # Continue processing other pages
                        continue
                        
        except InvalidPDFError:
            # Re-raise our custom exceptions
            raise
        except FileNotFoundError:
            self.logger.error(f"PDF file not found: {file_path}")
            raise FileProcessingError(f"PDF file not found: {file_path}", ErrorCodes.FILE_NOT_FOUND)
        except PermissionError:
            self.logger.error(f"Permission denied when accessing PDF: {file_path}")
            raise FileProcessingError(f"Permission denied when accessing PDF", ErrorCodes.FILE_PROCESSING_FAILED)
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle password-protected PDFs
            if "password" in error_msg or "encrypted" in error_msg:
                self.logger.error(f"PDF is password-protected or encrypted: {file_path}")
                raise FileProcessingError(
                    "PDF is password-protected. Please provide an unprotected PDF.",
                    ErrorCodes.INVALID_PDF_FORMAT
                )
            
            # Handle corrupted PDFs
            elif "invalid" in error_msg or "corrupt" in error_msg or "damaged" in error_msg:
                self.logger.error(f"PDF file appears to be corrupted: {file_path}")
                raise InvalidPDFError(file_path)
            
            # Handle other pdfplumber-specific errors
            elif "pdf" in error_msg:
                self.logger.error(f"PDF processing error: {e}")
                raise FileProcessingError(
                    f"Failed to process PDF file: {str(e)}",
                    ErrorCodes.INVALID_PDF_FORMAT
                )
            
            # Generic error
            else:
                self.logger.error(f"Unexpected error extracting tables from PDF: {e}")
                raise FileProcessingError(
                    f"Failed to extract data from PDF: {str(e)}",
                    ErrorCodes.PDF_PARSING_FAILED
                )
            
        return tables
    
    def _find_transaction_tables(self, tables: List[List[List[str]]]) -> List[List[List[str]]]:
        """Find all tables containing transactions"""
        transaction_tables = []
        for table in tables:
            if not table or len(table) < 2:
                continue
                
            # Look for transaction table indicators
            for row in table[:3]:  # Check first 3 rows for headers
                if row and any(self._is_transaction_header(cell) for cell in row if cell):
                    transaction_tables.append(table)
                    break  # Found a transaction table, move to next table

        return transaction_tables
    
    def _is_transaction_header(self, cell: str) -> bool:
        """Check if cell contains transaction table header indicators"""
        if not cell:
            return False
            
        cell_lower = str(cell).lower()
        
        # Get bank-specific headers
        bank_headers_ua = get_headers_for_bank(self.bank_type.value, "ua")
        bank_headers_en = get_headers_for_bank(self.bank_type.value, "en")
        
        # Combine all headers for this bank
        all_headers = bank_headers_ua + bank_headers_en
        
        return any(indicator in cell_lower for indicator in all_headers)
    
    def _parse_mcc_code(self, mcc_str: str) -> Optional[int]:
        """Parse MCC code string to integer"""
        try:
            if not mcc_str:
                return None
                
            # Clean MCC string (remove spaces, extract only digits)
            cleaned_mcc = re.sub(r'[^\d]', '', mcc_str.strip())
            
            if not cleaned_mcc:
                return None
                
            mcc_code = int(cleaned_mcc)
            
            # Validate MCC code range (0001-9999, 4 digits)
            # Valid MCC codes can start with 0 (e.g., 0742 for veterinary services)
            if 1 <= mcc_code <= 9999:
                return mcc_code
            else:
                self.logger.warning(f"MCC code {mcc_code} is outside valid range (0001-9999)")
                return None
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse MCC code '{mcc_str}': {e}")
            return None
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize transaction description"""
        if not description:
            return ""
            
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', str(description).strip())
        
        # Remove common prefixes/suffixes that don't add value
        prefixes_to_remove = [
            r'^[A-Z]{2,}\s*\|',  # Remove "ZMIST |" type prefixes
            r'^\d+\s*',  # Remove leading numbers
        ]
        
        for pattern in prefixes_to_remove:
            cleaned = re.sub(pattern, '', cleaned).strip()
            
        return cleaned
