from typing import List, Optional
from app.models.transaction import ParsedTransaction, BankType, TransactionType
from app.config.bank_headers import get_patterns_for_bank
from .base_parser import BasePDFParser

class MonobankParser(BasePDFParser):
    """Parser for Monobank PDF statements"""
    
    def __init__(self):
        super().__init__(BankType.MONOBANK)
    
    async def parse_pdf(self, file_path: str) -> List[ParsedTransaction]:
        """Parse Monobank PDF and extract transactions"""
        try:
            tables = self._extract_tables_from_pdf(file_path)
            transaction_tables = self._find_transaction_tables(tables)
            
            if not transaction_tables:
                self.logger.warning("No transaction tables found in Monobank PDF")
                return []
            
            self.logger.info(f"Found {len(transaction_tables)} transaction tables in Monobank PDF")
            return self._extract_transactions_from_tables(transaction_tables)
            
        except Exception as e:
            self.logger.error(f"Error parsing Monobank PDF: {e}")
            raise
    
    def _extract_transactions_from_table(self, table: List[List[str]]) -> List[ParsedTransaction]:
        """Extract transactions from Monobank table"""
        transactions = []
        
        # Find header row using bank-specific headers
        header_row = None
        for i, row in enumerate(table):
            if row and any(self._is_transaction_header(cell) for cell in row if cell):
                header_row = i
                break
        
        if header_row is None:
            self.logger.warning("Could not find Monobank transaction header")
            return []
        
        # Process transaction rows
        for row in table[header_row + 1:]:
            if not row or len(row) < 4:
                continue
                
            try:
                transaction = self._parse_transaction_row(row)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                self.logger.warning(f"Failed to parse Monobank transaction row: {e}")
                continue
        
        self.logger.info(f"Successfully parsed {len(transactions)} Monobank transactions")
        return transactions
    
    def _parse_transaction_row(self, row: List[str]) -> Optional[ParsedTransaction]:
        """Parse a single Monobank transaction row"""
        try:
            # Monobank table structure:
            # 0: Date and time, 1: Operation details, 2: MCC, 3: Amount in UAH, 
            # 4: Amount in operation currency, 5: Currency, 6: Rate, 7: Commission, 
            # 8: Cashback, 9: Balance after operation
            
            if len(row) < 4:
                return None
            
            # Parse date
            date_str = str(row[0]).strip() if row[0] else ""
            transaction_date = self._parse_date(date_str)
            
            # Parse description
            description = self._clean_description(str(row[1]).strip() if row[1] else "")
            
            # Parse amount in UAH (column 3)
            amount_str = str(row[3]).strip() if row[3] else ""
            amount = self._parse_amount(amount_str)
            
            
            # Determine transaction type
            transaction_type = self._calculate_transaction_type(amount, row)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(description, transaction_date, amount)
            
            # Create raw text for debugging
            raw_text = f"{date_str} | {description} | {amount_str}"
            
            return ParsedTransaction(
                amount=abs(amount),  # Store absolute amount
                description=description,
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                bank_type=self.bank_type,
                raw_text=raw_text,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing Monobank transaction row: {e}")
            return None
    
    def _calculate_transaction_type(self, amount: float, row: List[str]) -> TransactionType:
        """Determine transaction type for Monobank"""
        # Monobank uses negative amounts for expenses, positive for income
        if amount < 0:
            return TransactionType.EXPENSE