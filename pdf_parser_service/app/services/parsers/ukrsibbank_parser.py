import re
from typing import List, Optional
from app.models.transaction import ParsedTransaction, BankType, TransactionType
from .base_parser import BasePDFParser


# Separator pattern used in multiline descriptions
_SEPARATOR_RE = re.compile(r"[_ ]{10,}")

_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


class UkrsibBankParser(BasePDFParser):
    """Parser for UKRSIBBANK PDF statements.

    UKRSIBBANK PDFs contain two table types:
    - 6-column: account operations (Операції за картковим рахунком)
    - 7-column: card operations (Операції за платіжними картками)

    Both share the same last-column semantics: amount in account currency (UAH).
    """

    def __init__(self):
        super().__init__(BankType.UKRSIBBANK)

    async def parse_pdf(
        self, file_path: str, language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Parse UKRSIBBANK PDF and extract transactions from all tables."""
        tables = self._extract_tables_from_pdf(file_path)

        if not tables:
            self.logger.warning("No tables found in UKRSIBBANK PDF")
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
            f"Successfully parsed {len(transactions)} UKRSIBBANK transactions"
        )
        return transactions

    async def _extract_transactions_from_table(
        self, table: List[List[str]], language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Not used: UKRSIBBANK uses row-by-row parsing via parse_pdf directly.
        Required by BasePDFParser abstract interface."""
        return []

    # ------------------------------------------------------------------
    # Row parsing
    # ------------------------------------------------------------------

    def _parse_row(
        self, row: List[Optional[str]]
    ) -> Optional[ParsedTransaction]:
        """Parse a single row from either 6-col or 7-col table.

        Detects column layout per-row to handle ragged pdfplumber output.
        """
        if not row:
            return None

        # First cell must contain a date (DD.MM.YYYY) — this also
        # filters out header rows, empty rows, and summary rows ("Разом...")
        date_cell = (row[0] or "").strip()
        if not _DATE_RE.match(date_cell):
            return None

        # Determine column layout per-row
        row_len = len(row)
        if row_len >= 7:
            # Card operations: date | date2 | auth_code | description | currency | amount | amount_uah
            description_raw = row[3]
            currency = (row[4] or "UAH").strip()
            amount_str = row[6]  # amount in account currency (UAH)
        elif row_len >= 6:
            # Account operations: date | date2 | description | currency | amount | amount_uah
            description_raw = row[2]
            currency = (row[3] or "UAH").strip()
            amount_str = row[5]  # amount in account currency (UAH)
        else:
            return None

        # Parse date
        transaction_date = self._parse_date(date_cell)
        if transaction_date is None:
            return None

        # Parse amount (last column — always in account currency)
        if not amount_str or not amount_str.strip():
            # Some rows (e.g. "Виникнення заборгованості") have empty last col
            return None

        amount = self._parse_ukrsib_amount(amount_str)
        if amount is None or amount == 0:
            self.logger.warning(f"Skipping row with zero/unparseable amount: {amount_str}")
            return None

        # Transaction type
        transaction_type = (
            TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
        )

        # Clean description
        description = self._clean_ukrsib_description(description_raw)
        if not description:
            description = "UKRSIBBANK transaction"

        # Confidence
        confidence_score = self._calculate_confidence_score(
            description, transaction_date, amount
        )

        raw_text = f"{date_cell} | {description} | {amount_str} {currency}"

        return ParsedTransaction(
            amount=abs(amount),
            description=description,
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            bank_type=self.bank_type,
            raw_text=raw_text,
            confidence_score=confidence_score,
            mcc_code=None,
            mcc_category_name=None,
            mcc_category_translation=None,
            category_exists=False,
            category_id=None,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_ukrsib_amount(self, amount_str: str) -> Optional[float]:
        """Parse UKRSIBBANK amount string like '-7 605.00' or '158 571.00'."""
        try:
            cleaned = (
                amount_str.strip()
                .replace("\xa0", "")
                .replace(" ", "")
                .replace(",", ".")
            )
            return float(cleaned)
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Failed to parse UKRSIBBANK amount '{amount_str}': {e}")
            return None

    def _clean_ukrsib_description(self, raw: Optional[str]) -> str:
        """Clean multiline UKRSIBBANK description.

        Removes the '_ _ _ _ ...' separator line, joins remaining parts,
        then normalizes via the base class _clean_description.
        """
        if not raw:
            return ""

        lines = raw.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not _SEPARATOR_RE.match(stripped):
                cleaned_lines.append(stripped)

        joined = " ".join(cleaned_lines)
        return self._clean_description(joined)
