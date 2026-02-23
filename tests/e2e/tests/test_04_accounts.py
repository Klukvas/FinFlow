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
