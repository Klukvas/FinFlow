import re
from typing import List, Optional
from app.models.transaction import ParsedTransaction, BankType, TransactionType
from .base_parser import BasePDFParser


_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

# Descriptions that represent credit limit changes, not real transactions
_CREDIT_LIMIT_PREFIX = "збільшення кредитного ліміту"


class ABankParser(BasePDFParser):
    """Parser for A-Bank (Акцент-Банк) PDF statements.

    A-Bank PDFs have 11-column tables:
    0: Date+time  1: Card number  2: Description  3: MCC
    4: Amount UAH  5: Amount op currency  6: Currency  7: Rate
    8: Commission  9: Cashback  10: Balance after
    """

    def __init__(self):
        super().__init__(BankType.ABANK)

    async def parse_pdf(
        self, file_path: str, language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Parse A-Bank PDF and extract transactions."""
        tables = self._extract_tables_from_pdf(file_path)

        if not tables:
            self.logger.warning("No tables found in A-Bank PDF")
            return []

        transactions: List[ParsedTransaction] = []

        for table in tables:
            if not table:
                continue

            for row in table:
                tx = self._parse_row(row)
                if tx:
                    transactions.append(tx)

        self.logger.info(
            f"Successfully parsed {len(transactions)} A-Bank transactions"
        )
        return transactions

    async def _extract_transactions_from_table(
        self, table: List[List[str]], language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Not used: A-Bank uses row-by-row parsing via parse_pdf directly.
        Required by BasePDFParser abstract interface."""
        return []

    # ------------------------------------------------------------------
    # Row parsing
    # ------------------------------------------------------------------

    def _parse_row(self, row: List[Optional[str]]) -> Optional[ParsedTransaction]:
        """Parse a single A-Bank transaction row (11 columns)."""
        if not row or len(row) < 11:
            return None

        # First cell must contain a date (DD.MM.YYYY)
        date_cell = (row[0] or "").strip()
        if not _DATE_RE.match(date_cell):
            return None

        # Description
        description_raw = (row[2] or "").strip()

        # Skip credit limit change rows — not real transactions
        if description_raw.lower().startswith(_CREDIT_LIMIT_PREFIX):
            self.logger.info(f"Skipping credit limit change: {description_raw}")
            return None

        # Parse date (date cell may contain time on next line: "23.12.2025\n10:33")
        transaction_date = self._parse_date(date_cell)
        if transaction_date is None:
            return None

        # Parse amount (col 4 — amount in card currency UAH)
        amount_str = (row[4] or "").strip()
        amount = self._parse_abank_amount(amount_str)
        if amount is None or amount == 0:
            self.logger.warning(f"Skipping row with zero/unparseable amount: {amount_str}")
            return None

        # Transaction type
        transaction_type = (
            TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
        )

        # MCC code (col 3)
        mcc_code = self._parse_mcc_code(row[3]) if row[3] else None

        # Currency (col 6)
        currency = (row[6] or "UAH").strip()

        # Clean description
        description = self._clean_description(description_raw) or "A-Bank transaction"

        # Confidence
        confidence_score = self._calculate_confidence_score(
            description, transaction_date, amount
        )

        raw_text = (
            f"{date_cell} | {description} | MCC:{mcc_code} | {amount_str} {currency}"
        )

        return ParsedTransaction(
            amount=abs(amount),
            description=description,
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            bank_type=self.bank_type,
            raw_text=raw_text,
            confidence_score=confidence_score,
            mcc_code=mcc_code,
            mcc_category_name=None,
            mcc_category_translation=None,
            category_exists=False,
            category_id=None,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_abank_amount(self, amount_str: str) -> Optional[float]:
        """Parse A-Bank amount string like '-16 130.24' or '50 000.00'."""
        try:
            cleaned = (
                amount_str.strip()
                .replace("\xa0", "")
                .replace(" ", "")
                .replace(",", ".")
            )
            return float(cleaned)
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Failed to parse A-Bank amount '{amount_str}': {e}")
            return None
