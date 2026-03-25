"""E2E tests for account CRUD and balance tracking."""
import pytest

from tests.e2e.helpers.test_data import account_name

pytestmark = pytest.mark.account


class TestAccountCRUD:

    async def test_create_account(self, account_client, shared_account):
        """Shared account was created in conftest; verify it exists."""
        result = await account_client.list_all()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert any(a["id"] == shared_account["id"] for a in data)

    async def test_list_accounts(self, account_client, shared_account):
        result = await account_client.list_all()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert any(a["id"] == shared_account["id"] for a in data)

    async def test_get_account_by_id(self, account_client, shared_account):
        result = await account_client.get(shared_account["id"])
        data = result.raise_on_error()
        assert data["id"] == shared_account["id"]

    async def test_update_account(self, account_client, shared_account):
        new_name = account_name()
        result = await account_client.update(shared_account["id"], name=new_name)
        data = result.raise_on_error()
        assert data["name"] == new_name

    async def test_account_summaries(self, account_client, shared_account):
        result = await account_client.summaries()
        assert result.ok

    async def test_account_statistics(self, account_client):
        result = await account_client.statistics()
        assert result.ok

    async def test_account_limit_enforced(self, account_client, shared_account):
        """Basic plan limits to 2 accounts; exceeding the limit should fail."""
        # shared_account already uses one slot; try to create beyond limit
        results = []
        for _ in range(3):
            r = await account_client.create(account_name())
            results.append(r)
            if not r.ok:
                break
        # At least the last attempt should fail
        assert any(not r.ok for r in results), "Account limit was not enforced"
        # Clean up any we successfully created
        for r in results:
            if r.ok:
                await account_client.archive(r.data["id"])


class TestAccountArchive:

    async def test_archive_account(self, account_client):
        """Create an account, archive it, and verify it is no longer active."""
        created = (await account_client.create(account_name())).raise_on_error()
        result = await account_client.archive(created["id"])
        assert result.ok or result.status_code in (200, 204)

        # After archiving, the account should either not appear in the
        # default list or be marked as archived
        listed = (await account_client.list_all()).raise_on_error()
        active_ids = [a["id"] for a in listed if not a.get("is_archived")]
        assert created["id"] not in active_ids


class TestAccountTransactions:

    async def test_get_account_transactions(
        self, account_client, expense_client, shared_account, shared_expense_category,
    ):
        """Account transactions endpoint returns linked expenses."""
        # Create an expense linked to the shared account
        await expense_client.create(
            amount=12.34,
            category_id=shared_expense_category["id"],
            account_id=shared_account["id"],
            description="Txn test",
        )
        result = await account_client.transactions(shared_account["id"])
        assert result.ok


class TestAccountSummary:

    async def test_get_single_account_summary(self, account_client, shared_account):
        """Single-account summary endpoint returns data for one account."""
        result = await account_client.summary(shared_account["id"])
        assert result.ok
