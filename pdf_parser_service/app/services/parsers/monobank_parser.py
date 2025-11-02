from typing import List, Optional, Dict, Any
from app.models.transaction import ParsedTransaction, BankType, TransactionType
from app.config.bank_headers import get_patterns_for_bank
from app.clients.category_client import CategoryServiceClient
from .base_parser import BasePDFParser

class MonobankParser(BasePDFParser):
    """Parser for Monobank PDF statements"""
    
    def __init__(self):
        super().__init__(BankType.MONOBANK)
        self.category_client = CategoryServiceClient()
    
    async def parse_pdf(self, file_path: str, language: str = "en", user_id: int = None) -> List[ParsedTransaction]:
        """Parse Monobank PDF and extract transactions"""
        try:
            tables = self._extract_tables_from_pdf(file_path)
            transaction_tables = self._find_transaction_tables(tables)
            
            if not transaction_tables:
                self.logger.warning("No transaction tables found in Monobank PDF")
                return []
            
            self.logger.info(f"Found {len(transaction_tables)} transaction tables in Monobank PDF")
            return await self._extract_transactions_from_tables(transaction_tables, language, user_id)
            
        except Exception as e:
            self.logger.error(f"Error parsing Monobank PDF: {e}")
            raise
    
    async def _extract_transactions_from_table(self, table: List[List[str]], language: str = "en", user_id: int = None) -> List[ParsedTransaction]:
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
                transaction = await self._parse_transaction_row(row, language, user_id)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                self.logger.warning(f"Failed to parse Monobank transaction row: {e}")
                continue
        
        self.logger.info(f"Successfully parsed {len(transactions)} Monobank transactions")
        return transactions
    
    async def _parse_transaction_row(self, row: List[str], language: str = "en", user_id: int = None) -> Optional[ParsedTransaction]:
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
            
            # Parse MCC code (column 2)
            mcc_code = self._parse_mcc_code(str(row[2]).strip() if row[2] else "")
            
            # Parse amount in UAH (column 3)
            amount_str = str(row[3]).strip() if row[3] else ""
            amount = self._parse_amount(amount_str)
            
            # Skip if amount couldn't be parsed
            if amount is None:
                self.logger.warning(f"Skipping row with invalid amount: {amount_str}")
                return None
            
            # Determine transaction type
            transaction_type = self._calculate_transaction_type(amount, row)
            
            # Get MCC category information
            mcc_category_name = None
            mcc_category_translation = None
            if mcc_code:
                try:
                    category_info = await self.category_client.get_mcc_category(mcc_code, language)
                    if category_info:
                        mcc_category_name = category_info.get("name")
                        mcc_category_translation = category_info.get("translation")
                        self.logger.info(f"Found category for MCC {mcc_code}: {mcc_category_name} ({mcc_category_translation} {language})")
                    else:
                        self.logger.warning(f"No category found for MCC code {mcc_code}")
                except Exception as e:
                    self.logger.error(f"Error getting category for MCC {mcc_code}: {e}")
            
            # Check if user already has a category with this MCC code and get category ID
            category_exists = False
            category_id = None
            if mcc_code and user_id:
                try:
                    category_info = await self.category_client.get_category_by_mcc(mcc_code, user_id)
                    if category_info:
                        category_exists = category_info.get("exists", False)
                        category_id = category_info.get("category_id")
                        self.logger.info(f"Category info for MCC {mcc_code}: exists={category_exists}, id={category_id}")
                    else:
                        self.logger.warning(f"No category info returned for MCC code {mcc_code}")
                except Exception as e:
                    self.logger.error(f"Error getting category info for MCC {mcc_code}: {e}")
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(description, transaction_date, amount)
            
            # Create raw text for debugging
            raw_text = f"{date_str} | {description} | MCC:{mcc_code} | {amount_str}"
            
            return ParsedTransaction(
                amount=abs(amount),  # Store absolute amount
                description=description,
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                bank_type=self.bank_type,
                raw_text=raw_text,
                confidence_score=confidence_score,
                mcc_code=mcc_code,
                mcc_category_name=mcc_category_name,
                mcc_category_translation=mcc_category_translation,
                category_exists=category_exists,
                category_id=category_id
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing Monobank transaction row: {e}")
            return None

    async def _get_mcc_categories_batch(self, mcc_codes: List[int], language: str) -> Dict[int, Dict[str, Any]]:
        """Get MCC category information for multiple codes in batch"""
        try:
            # Get all MCC codes and filter for the ones we need
            response = await self.category_client.get_mcc_category(mcc_codes[0], language)  # This gets all codes
            if not response:
                return {}
            
            # Since the current API gets all codes, we need to filter
            # This is a temporary solution - ideally we'd have a batch endpoint
            mcc_info = {}
            for mcc_code in mcc_codes:
                try:
                    category_info = await self.category_client.get_mcc_category(mcc_code, language)
                    if category_info:
                        mcc_info[mcc_code] = category_info
                except Exception as e:
                    self.logger.warning(f"Failed to get MCC info for {mcc_code}: {e}")
            
            return mcc_info
        except Exception as e:
            self.logger.error(f"Error getting MCC categories in batch: {e}")
            return {}

    async def _get_user_categories_batch(self, mcc_codes: List[int], user_id: int) -> Dict[int, Dict[str, Any]]:
        """Get user's existing categories for multiple MCC codes in batch"""
        try:
            results = await self.category_client.check_categories_exist_by_mcc_batch(mcc_codes, user_id)
            if not results:
                return {}
            
            # Convert list to dict for easy lookup
            mcc_categories = {}
            for result in results:
                mcc_code = result.get('mcc_code')
                if mcc_code:
                    mcc_categories[mcc_code] = result
            
            return mcc_categories
        except Exception as e:
            self.logger.error(f"Error getting user categories in batch: {e}")
            return {}
    
    def _calculate_transaction_type(self, amount: float, row: List[str]) -> TransactionType:
        """Determine transaction type for Monobank"""
        # Monobank uses negative amounts for expenses, positive for income
        if amount < 0:
            return TransactionType.EXPENSE
        else:
            return TransactionType.INCOME