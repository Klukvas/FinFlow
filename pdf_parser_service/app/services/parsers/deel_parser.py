import csv
from typing import List, Optional
from datetime import date, datetime

from app.models.transaction import ParsedTransaction, BankType, TransactionType
from .base_parser import BasePDFParser


_STATUS_COMPLETED = "completed"
_TYPE_CLIENT_PAYMENT = "client_payment"
_TYPE_WITHDRAWAL = "withdrawal"
_FORMULA_PREFIXES = ("=", "+", "@", "|", "\t", "\r")


class DeelParser(BasePDFParser):
    """Parser for Deel CSV transaction exports"""

    def __init__(self):
        super().__init__(BankType.DEEL)

    async def parse_pdf(
        self, file_path: str, language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Parse Deel CSV file and extract transactions"""
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                transactions: List[ParsedTransaction] = []

                for row_idx, row in enumerate(reader, start=2):
                    try:
                        transaction = self._parse_csv_row(row, row_idx)
                        if transaction is not None:
                            transactions.append(transaction)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to parse Deel row {row_idx}: {e}"
                        )
                        continue

            self.logger.info(
                f"Successfully parsed {len(transactions)} Deel transactions"
            )
            return transactions

        except UnicodeDecodeError:
            self.logger.error("Failed to decode Deel CSV — not valid UTF-8")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing Deel CSV: {e}")
            raise

    async def _extract_transactions_from_table(
        self, table: List[List[str]], language: str = "en", user_id: int = None
    ) -> List[ParsedTransaction]:
        """Not used for CSV flow — required by abstract base class"""
        return []

    def _parse_csv_row(
        self, row: dict, row_idx: int
    ) -> Optional[ParsedTransaction]:
        """Parse a single Deel CSV row.

        Key columns:
        - Date Requested: YYYY-MM-DD HH:MM:SS
        - Transaction Status: completed | cancelled
        - Transaction Type: client_payment | withdrawal
        - Currency: EUR | USD
        - Transaction Amount: signed float (positive = income, negative = expense)
        - Provider Fee: fee amount
        - Client: payer name (for income)
        - Contract Name: contract holder
        - Withdraw Method: payoneer | bank_transfer | deel_card
        - Withdraw Method Custom Name: custom label for withdrawal
        """
        # Skip non-completed transactions
        status = (row.get("Transaction Status") or "").strip().lower()
        if status != _STATUS_COMPLETED:
            return None

        # --- date ---
        date_str = (row.get("Date Requested") or "").strip()
        transaction_date = self._parse_deel_date(date_str)
        if transaction_date is None:
            self.logger.warning(
                f"Row {row_idx}: could not parse date '{date_str}'"
            )
            return None

        # --- amount ---
        amount_str = (row.get("Transaction Amount") or "").strip()
        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            self.logger.warning(
                f"Row {row_idx}: could not parse amount '{amount_str}'"
            )
            return None

        if amount == 0:
            return None

        # --- transaction type ---
        tx_type_str = (row.get("Transaction Type") or "").strip().lower()
        if tx_type_str == _TYPE_CLIENT_PAYMENT:
            transaction_type = TransactionType.INCOME
        elif tx_type_str == _TYPE_WITHDRAWAL:
            transaction_type = TransactionType.EXPENSE
        else:
            # Unknown type — infer from sign
            transaction_type = (
                TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
            )

        # --- currency ---
        currency = (row.get("Currency") or "EUR").strip()

        # --- description (includes currency prefix for multi-currency clarity) ---
        base_description = self._build_description(row, transaction_type)
        description = f"[{currency}] {base_description}"

        # --- provider fee ---
        fee_str = (row.get("Provider Fee") or "").strip()
        provider_fee = None
        if fee_str:
            try:
                provider_fee = float(fee_str)
            except (ValueError, TypeError):
                pass

        # --- confidence ---
        confidence_score = self._calculate_confidence_score(
            description, transaction_date, amount
        )

        # --- raw text ---
        raw_text = (
            f"{date_str} | {tx_type_str} | {description} | "
            f"{amount_str} {currency}"
        )
        if provider_fee and provider_fee > 0:
            raw_text += f" (fee: {provider_fee})"

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

    def _parse_deel_date(self, date_str: str) -> Optional[date]:
        """Parse Deel date format YYYY-MM-DD HH:MM:SS"""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.date()
        except ValueError:
            # Fallback: try date-only format
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.date()
            except ValueError:
                return None

    def _sanitize_field(self, value: str) -> str:
        """Strip leading formula-injection characters from a field value"""
        v = value.strip()
        while v and v[0] in _FORMULA_PREFIXES:
            v = v[1:].strip()
        return v

    def _build_description(
        self, row: dict, transaction_type: TransactionType
    ) -> str:
        """Build human-readable description from CSV row fields"""
        if transaction_type == TransactionType.INCOME:
            client = self._sanitize_field(row.get("Client") or "")
            contract = self._sanitize_field(row.get("Contract Name") or "")
            if client and contract:
                return f"[Payment] {client} — {contract}"
            if client:
                return f"[Payment] {client}"
            if contract:
                return f"[Payment] {contract}"
            return "Deel payment"
        else:
            method = self._sanitize_field(row.get("Withdraw Method") or "")
            custom_name = self._sanitize_field(
                row.get("Withdraw Method Custom Name") or ""
            )
            label = custom_name or method or "withdrawal"
            return f"[Withdrawal] {label}"
