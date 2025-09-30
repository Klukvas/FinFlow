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
    async def parse_pdf(self, file_path: str) -> List[ParsedTransaction]:
        """Parse PDF file and extract transactions"""
        pass
    
    @abstractmethod
    def _extract_transactions_from_table(self, table: List[List[str]]) -> List[ParsedTransaction]:
        """Extract transactions from a parsed table"""
        pass
    
    def _extract_transactions_from_tables(self, tables: List[List[List[str]]]) -> List[ParsedTransaction]:
        """Extract transactions from multiple tables"""
        all_transactions = []
        
        for i, table in enumerate(tables):
            self.logger.info(f"Processing table {i + 1}/{len(tables)}")
            try:
                transactions = self._extract_transactions_from_table(table)
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
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            self.logger.error(f"Failed to extract tables from PDF: {e}")
            raise
            
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
