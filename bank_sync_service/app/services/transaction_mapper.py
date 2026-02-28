from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.monobank import MonobankStatementItem
from app.services.monobank_client import numeric_to_alpha_currency
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionMapper:
    @staticmethod
    def map_to_finflow(
        item: MonobankStatementItem,
        finflow_account_id: int,
        category_id: int | None = None,
    ) -> dict | None:
        # Skip hold (authorization) transactions — not yet completed
        if item.hold:
            return None

        amount_raw = item.amount
        amount = Decimal(str(abs(amount_raw))) / 100
        currency = numeric_to_alpha_currency(item.currencyCode)
        tx_date = datetime.fromtimestamp(item.time, tz=timezone.utc).date().isoformat()

        description = item.description
        if item.comment:
            description = f"{description} ({item.comment})"

        is_expense = amount_raw < 0

        base_data = {
            "amount": str(amount),
            "currency": currency,
            "date": tx_date,
            "description": description,
            "account_id": finflow_account_id,
        }

        if category_id is not None:
            base_data["category_id"] = category_id

        return {
            "type": "expense" if is_expense else "income",
            "data": base_data,
            "external_id": item.id,
            "mcc": item.mcc,
        }

