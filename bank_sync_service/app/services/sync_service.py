from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.bank_connection import BankConnection
from app.models.linked_account import LinkedAccount
from app.models.sync_log import SyncLog
from app.models.synced_transaction import SyncedTransaction
from app.services.encryption import encryption
from app.services.monobank_client import monobank_client, numeric_to_alpha_currency
from app.services.transaction_mapper import TransactionMapper
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.exceptions import (
    ConnectionNotFoundError,
    LinkedAccountNotFoundError,
    SyncLogNotFoundError,
    TokenValidationError,
    MonobankApiError,
    AccountNotLinkedError,
    SyncInProgressError,
    RateLimitError,
    ExternalServiceError,
    TransactionLimitExceededError,
)
from app.utils.logger import get_logger
from shared.auth.workspace_auth import WorkspaceAuthorizationMixin

logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SyncService(WorkspaceAuthorizationMixin):
    def __init__(self, db: Session):
        super().__init__(
            access_denied_error=lambda msg: TokenValidationError(msg),
            workspace_mismatch_error=lambda msg: TokenValidationError(msg),
        )
        self.db = db
        self.expense_client = ExpenseServiceClient()
        self.income_client = IncomeServiceClient()
        self.category_client = CategoryServiceClient()
        self.mapper = TransactionMapper()

    async def connect(self, user_id: int, workspace_id: UUID, token: str) -> BankConnection:
        self.authorize_workspace_access(workspace_id, user_id, required_role="member")

        # Validate token by fetching client info
        try:
            client_info = await monobank_client.get_client_info(token)
        except (RateLimitError, TokenValidationError, MonobankApiError):
            raise
        except Exception:
            logger.error("Unexpected error during token validation", exc_info=True)
            raise TokenValidationError("Unable to validate token — please check it is correct")

        encrypted_token = encryption.encrypt(token)

        connection = BankConnection(
            user_id=user_id,
            workspace_id=workspace_id,
            bank_type="monobank",
            encrypted_token=encrypted_token,
            client_name=client_info.name,
            client_id=client_info.clientId,
            is_active=True,
        )
        self.db.add(connection)
        self.db.flush()

        # Create linked accounts from Monobank accounts
        for account in client_info.accounts:
            masked_pan = ", ".join(account.maskedPan) if account.maskedPan else None
            currency = numeric_to_alpha_currency(account.currencyCode)

            linked = LinkedAccount(
                connection_id=connection.id,
                external_account_id=account.id,
                account_name=f"{currency} ({account.type or 'card'})",
                currency_code=account.currencyCode,
                currency=currency,
                masked_pan=masked_pan,
                iban=account.iban,
                is_synced=True,
            )
            self.db.add(linked)

        self.db.commit()
        self.db.refresh(connection)
        return connection

    def get_connections(self, user_id: int, workspace_id: UUID) -> list[BankConnection]:
        return (
            self.db.query(BankConnection)
            .filter(
                BankConnection.user_id == user_id,
                BankConnection.workspace_id == workspace_id,
                BankConnection.is_active.is_(True),
            )
            .order_by(desc(BankConnection.created_at))
            .all()
        )

    def get_connection(self, connection_id: int, user_id: int, workspace_id: UUID) -> BankConnection:
        connection = (
            self.db.query(BankConnection)
            .filter(
                BankConnection.id == connection_id,
                BankConnection.user_id == user_id,
                BankConnection.workspace_id == workspace_id,
                BankConnection.is_active.is_(True),
            )
            .first()
        )
        if not connection:
            raise ConnectionNotFoundError(connection_id)
        return connection

    def disconnect(self, connection_id: int, user_id: int, workspace_id: UUID) -> None:
        connection = self.get_connection(connection_id, user_id, workspace_id)

        active_sync = (
            self.db.query(SyncLog)
            .filter(
                SyncLog.connection_id == connection.id,
                SyncLog.status.in_(["pending", "in_progress"]),
            )
            .first()
        )
        if active_sync:
            raise SyncInProgressError(connection_id)

        connection.is_active = False
        self.db.commit()

    def link_account(
        self,
        connection_id: int,
        linked_account_id: int,
        finflow_account_id: int,
        user_id: int,
        workspace_id: UUID,
    ) -> LinkedAccount:
        connection = self.get_connection(connection_id, user_id, workspace_id)

        linked = (
            self.db.query(LinkedAccount)
            .filter(
                LinkedAccount.id == linked_account_id,
                LinkedAccount.connection_id == connection.id,
            )
            .first()
        )
        if not linked:
            raise LinkedAccountNotFoundError(linked_account_id)

        linked.finflow_account_id = finflow_account_id
        self.db.commit()
        self.db.refresh(linked)
        return linked

    def toggle_account_sync(
        self,
        connection_id: int,
        linked_account_id: int,
        user_id: int,
        workspace_id: UUID,
    ) -> LinkedAccount:
        connection = self.get_connection(connection_id, user_id, workspace_id)

        linked = (
            self.db.query(LinkedAccount)
            .filter(
                LinkedAccount.id == linked_account_id,
                LinkedAccount.connection_id == connection.id,
            )
            .first()
        )
        if not linked:
            raise LinkedAccountNotFoundError(linked_account_id)

        linked.is_synced = not linked.is_synced
        self.db.commit()
        self.db.refresh(linked)
        return linked

    def _get_linked_accounts(
        self, connection: BankConnection, account_ids: list[int] | None = None,
    ) -> list[LinkedAccount]:
        """Get linked accounts that are synced and mapped to FinFlow accounts."""
        query = self.db.query(LinkedAccount).filter(
            LinkedAccount.connection_id == connection.id,
            LinkedAccount.is_synced.is_(True),
        )
        if account_ids:
            query = query.filter(LinkedAccount.id.in_(account_ids))
        accounts = query.all()

        unlinked = [a for a in accounts if not a.finflow_account_id]
        if unlinked:
            logger.warning(
                f"Skipping {len(unlinked)} accounts not linked to FinFlow",
                extra={"connection_id": connection.id},
            )
        return [a for a in accounts if a.finflow_account_id]

    def _enforce_rate_limit(self, connection: BankConnection) -> None:
        """Enforce minimum cooldown between syncs."""
        if connection.last_sync_at:
            last_sync = connection.last_sync_at
            if last_sync.tzinfo is None:
                last_sync = last_sync.replace(tzinfo=timezone.utc)
            elapsed = (_utcnow() - last_sync).total_seconds()
            if elapsed < 60:
                raise RateLimitError(int(60 - elapsed) + 1)

    def _check_no_active_sync(self, connection: BankConnection) -> None:
        """Raise if a sync is already in progress."""
        active_sync = (
            self.db.query(SyncLog)
            .filter(
                SyncLog.connection_id == connection.id,
                SyncLog.status.in_(["pending", "in_progress"]),
            )
            .first()
        )
        if active_sync:
            raise SyncInProgressError(connection.id)

    async def _fetch_and_map_transactions(
        self,
        connection: BankConnection,
        linked_accounts: list[LinkedAccount],
        user_id: int,
        workspace_id: UUID,
        days_back: int,
    ) -> tuple[list[dict], int, int]:
        """Fetch statements, deduplicate, map to FinFlow format, resolve MCC categories.

        Returns (mapped_transactions, total_found, total_skipped).
        """
        token = encryption.decrypt(connection.encrypted_token)
        now = _utcnow()
        all_mapped: list[dict] = []
        total_found = 0
        total_skipped = 0

        for linked_account in linked_accounts:
            from_ts = int((now - timedelta(days=days_back)).timestamp())
            to_ts = int(now.timestamp())

            await monobank_client.wait_for_rate_limit(token)

            statements = await monobank_client.get_statements(
                token,
                linked_account.external_account_id,
                from_ts,
                to_ts,
            )

            total_found += len(statements)

            # Batch deduplication
            external_ids = [item.id for item in statements]
            existing_ids: set[str] = set()
            if external_ids:
                existing_rows = (
                    self.db.query(SyncedTransaction.external_transaction_id)
                    .filter(
                        SyncedTransaction.connection_id == connection.id,
                        SyncedTransaction.external_transaction_id.in_(external_ids),
                    )
                    .all()
                )
                existing_ids = {row[0] for row in existing_rows}

            for item in statements:
                mapped = self.mapper.map_to_finflow(
                    item,
                    linked_account.finflow_account_id,
                )
                if mapped is None:
                    total_skipped += 1
                    continue

                if mapped["external_id"] in existing_ids:
                    total_skipped += 1
                    continue

                # Resolve MCC category
                cat_result = await self.category_client.get_category_by_mcc(
                    mapped["mcc"], user_id, str(workspace_id)
                )
                if cat_result and "id" in cat_result:
                    mapped["data"]["category_id"] = cat_result["id"]
                    mapped["category_id"] = cat_result["id"]
                    mapped["category_name"] = cat_result.get("name")

                all_mapped.append(mapped)

        return all_mapped, total_found, total_skipped

    async def preview_sync(
        self,
        connection_id: int,
        user_id: int,
        workspace_id: UUID,
        account_ids: list[int] | None = None,
        days_back: int = 30,
    ) -> dict:
        """Fetch and preview transactions without creating anything."""
        connection = self.get_connection(connection_id, user_id, workspace_id)
        self._enforce_rate_limit(connection)

        linked_accounts = self._get_linked_accounts(connection, account_ids)

        mapped_txns, total_found, total_skipped = await self._fetch_and_map_transactions(
            connection, linked_accounts, user_id, workspace_id, days_back
        )

        # Update last_sync_at so rate limit applies to preview calls too
        connection.last_sync_at = _utcnow()
        self.db.commit()

        transactions = [
            {
                "external_id": m["external_id"],
                "type": m["type"],
                "amount": m["data"]["amount"],
                "currency": m["data"].get("currency", "UAH"),
                "date": m["data"]["date"],
                "description": m["data"].get("description", ""),
                "mcc": m.get("mcc"),
                "category_id": m.get("category_id"),
                "category_name": m.get("category_name"),
                "account_id": m["data"]["account_id"],
            }
            for m in mapped_txns
        ]

        return {
            "transactions": transactions,
            "total_found": total_found,
            "total_new": len(mapped_txns),
            "total_skipped": total_skipped,
        }

    async def confirm_sync(
        self,
        connection_id: int,
        user_id: int,
        workspace_id: UUID,
        transactions: list[dict],
        days_back: int = 30,
    ) -> SyncLog:
        """Create selected transactions and record a SyncLog."""
        connection = self.get_connection(connection_id, user_id, workspace_id)
        self._check_no_active_sync(connection)

        now = _utcnow()
        sync_log = SyncLog(
            connection_id=connection.id,
            status="in_progress",
            sync_from=now - timedelta(days=days_back),
            sync_to=now,
        )
        self.db.add(sync_log)
        self.db.flush()

        total_imported = 0
        total_skipped = 0
        errors: list[str] = []
        expense_limit_hit = False
        income_limit_hit = False

        try:
            for txn in transactions:
                if txn["type"] == "expense" and expense_limit_hit:
                    total_skipped += 1
                    continue
                if txn["type"] == "income" and income_limit_hit:
                    total_skipped += 1
                    continue

                create_data = {
                    "amount": str(txn["amount"]),
                    "currency": txn.get("currency", "UAH"),
                    "date": str(txn["date"]),
                    "description": txn.get("description", ""),
                    "account_id": txn["account_id"],
                }
                if txn.get("category_id"):
                    create_data["category_id"] = txn["category_id"]

                try:
                    if txn["type"] == "expense":
                        result = await self.expense_client.create_expense(
                            create_data, user_id, str(workspace_id)
                        )
                    else:
                        result = await self.income_client.create_income(
                            create_data, user_id, str(workspace_id)
                        )

                    finflow_id = result.get("id", 0)

                    synced = SyncedTransaction(
                        connection_id=connection.id,
                        external_transaction_id=txn["external_id"],
                        finflow_type=txn["type"],
                        finflow_id=finflow_id,
                        amount=create_data["amount"],
                        date=create_data["date"],
                        description=create_data.get("description"),
                    )
                    self.db.add(synced)
                    total_imported += 1

                except TransactionLimitExceededError as e:
                    if e.transaction_type == "expense":
                        expense_limit_hit = True
                        errors.append("Expense limit reached. Upgrade your plan to sync more.")
                    elif e.transaction_type == "income":
                        income_limit_hit = True
                        errors.append("Income limit reached. Upgrade your plan to sync more.")
                    else:
                        logger.error(f"Unknown transaction type in limit error: {e.transaction_type}")
                    total_skipped += 1
                    logger.warning(f"Subscription limit hit for {e.transaction_type}")

                except Exception as e:
                    logger.error(f"Failed to create {txn['type']}: {e}")
                    errors.append(f"Failed to create {txn['type']}")
                    total_skipped += 1

        finally:
            sync_log.status = "completed" if not errors else "completed_with_errors"
            sync_log.transactions_found = len(transactions)
            sync_log.transactions_imported = total_imported
            sync_log.transactions_skipped = total_skipped
            sync_log.error_message = "; ".join(errors) if errors else None
            sync_log.completed_at = _utcnow()

            connection.last_sync_at = _utcnow()

            self.db.commit()
            self.db.refresh(sync_log)

        return sync_log

    async def sync_connection(
        self,
        connection_id: int,
        user_id: int,
        workspace_id: UUID,
        account_ids: list[int] | None = None,
        days_back: int = 30,
    ) -> SyncLog:
        connection = self.get_connection(connection_id, user_id, workspace_id)
        self._check_no_active_sync(connection)
        self._enforce_rate_limit(connection)

        linked_accounts = self._get_linked_accounts(connection, account_ids)

        now = _utcnow()
        sync_log = SyncLog(
            connection_id=connection.id,
            status="in_progress",
            sync_from=now - timedelta(days=days_back),
            sync_to=now,
        )
        self.db.add(sync_log)
        self.db.flush()

        total_found = 0
        total_imported = 0
        total_skipped = 0
        errors: list[str] = []
        expense_limit_hit = False
        income_limit_hit = False

        try:
            mapped_txns, total_found, total_skipped = await self._fetch_and_map_transactions(
                connection, linked_accounts, user_id, workspace_id, days_back
            )

            for mapped in mapped_txns:
                if mapped["type"] == "expense" and expense_limit_hit:
                    total_skipped += 1
                    continue
                if mapped["type"] == "income" and income_limit_hit:
                    total_skipped += 1
                    continue

                try:
                    if mapped["type"] == "expense":
                        result = await self.expense_client.create_expense(
                            mapped["data"], user_id, str(workspace_id)
                        )
                    else:
                        result = await self.income_client.create_income(
                            mapped["data"], user_id, str(workspace_id)
                        )

                    finflow_id = result.get("id", 0)

                    synced = SyncedTransaction(
                        connection_id=connection.id,
                        external_transaction_id=mapped["external_id"],
                        finflow_type=mapped["type"],
                        finflow_id=finflow_id,
                        amount=mapped["data"]["amount"],
                        date=mapped["data"]["date"],
                        description=mapped["data"].get("description"),
                    )
                    self.db.add(synced)
                    total_imported += 1

                except TransactionLimitExceededError as e:
                    if e.transaction_type == "expense":
                        expense_limit_hit = True
                        errors.append("Expense limit reached. Upgrade your plan to sync more.")
                    elif e.transaction_type == "income":
                        income_limit_hit = True
                        errors.append("Income limit reached. Upgrade your plan to sync more.")
                    else:
                        logger.error(f"Unknown transaction type in limit error: {e.transaction_type}")
                    total_skipped += 1
                    logger.warning(f"Subscription limit hit for {e.transaction_type}")

                except Exception as e:
                    logger.error(f"Failed to create {mapped['type']}: {e}")
                    errors.append(f"Failed to create {mapped['type']}")
                    total_skipped += 1

        finally:
            sync_log.status = "completed" if not errors else "completed_with_errors"
            sync_log.transactions_found = total_found
            sync_log.transactions_imported = total_imported
            sync_log.transactions_skipped = total_skipped
            sync_log.error_message = "; ".join(errors) if errors else None
            sync_log.completed_at = _utcnow()

            connection.last_sync_at = _utcnow()

            self.db.commit()
            self.db.refresh(sync_log)

        return sync_log

    def get_sync_status(self, connection_id: int, user_id: int, workspace_id: UUID) -> SyncLog | None:
        connection = self.get_connection(connection_id, user_id, workspace_id)
        return (
            self.db.query(SyncLog)
            .filter(SyncLog.connection_id == connection.id)
            .order_by(desc(SyncLog.started_at))
            .first()
        )

    def get_sync_history(
        self,
        connection_id: int,
        user_id: int,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[SyncLog]:
        connection = self.get_connection(connection_id, user_id, workspace_id)
        return (
            self.db.query(SyncLog)
            .filter(SyncLog.connection_id == connection.id)
            .order_by(desc(SyncLog.started_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
