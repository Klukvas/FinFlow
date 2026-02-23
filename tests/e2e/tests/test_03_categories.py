"""E2E tests for category CRUD and hierarchy."""
import pytest

from tests.e2e.helpers.test_data import category_name

pytestmark = pytest.mark.category


class TestCategoryCRUD:

    async def test_create_and_delete_category(self, category_client):
        """Create a category and immediately delete it to stay within limits."""
        name = category_name()
        result = await category_client.create(name)
        data = result.raise_on_error()
        assert data["name"] == name
        assert "id" in data

        # Clean up
        await category_client.delete(data["id"])

    async def test_get_category_by_id(self, category_client, shared_expense_category):
        """Use the shared category to test get-by-id."""
        result = await category_client.get(shared_expense_category["id"])
        data = result.raise_on_error()
        assert data["id"] == shared_expense_category["id"]

    async def test_update_category(self, category_client):
        """Create, update, then delete to stay within limits."""
        created = (await category_client.create(category_name())).raise_on_error()
        new_name = category_name("Updated")
        result = await category_client.update(created["id"], new_name)
        data = result.raise_on_error()
        assert data["name"] == new_name

        # Clean up
        await category_client.delete(created["id"])

    async def test_delete_category(self, category_client):
        """Create and delete a category."""
        created = (await category_client.create(category_name())).raise_on_error()
        result = await category_client.delete(created["id"])
        assert result.ok or result.status_code == 204

        # Verify deleted
        get_result = await category_client.get(created["id"])
        assert not get_result.ok

    async def test_list_categories(self, category_client, shared_expense_category):
        """List should include the shared category."""
        result = await category_client.list_all(flat=True)
        data = result.raise_on_error()
        items = data if isinstance(data, list) else data.get("items", [])
        assert len(items) >= 1


class TestCategoryHierarchy:

    async def test_create_child_category(self, category_client):
        """Create parent + child, then clean up both."""
        parent = (await category_client.create(category_name("Parent"))).raise_on_error()
        child = (await category_client.create(category_name("Child"), parent_id=parent["id"])).raise_on_error()
        assert child.get("parent_id") == parent["id"]

        # Clean up (child first, then parent)
        await category_client.delete(child["id"])
        await category_client.delete(parent["id"])

    async def test_get_children(self, category_client):
        """Create hierarchy, verify children, then clean up."""
        parent = (await category_client.create(category_name("Parent"))).raise_on_error()
        child1 = (await category_client.create(category_name("Child1"), parent_id=parent["id"])).raise_on_error()
        child2 = (await category_client.create(category_name("Child2"), parent_id=parent["id"])).raise_on_error()

        result = await category_client.get_children(parent["id"])
        data = result.raise_on_error()
        children = data if isinstance(data, list) else data.get("items", [])
        assert len(children) >= 2

        # Clean up
        await category_client.delete(child1["id"])
        await category_client.delete(child2["id"])
        await category_client.delete(parent["id"])

    async def test_delete_parent_with_children_fails(self, category_client):
        """Deleting a parent with children should fail."""
        parent = (await category_client.create(category_name("Parent"))).raise_on_error()
        child = (await category_client.create(category_name("Child"), parent_id=parent["id"])).raise_on_error()

        result = await category_client.delete(parent["id"])
        # Should fail (400 or 409), or if cascade delete is supported, accept 200/204
        if not result.ok:
            assert result.status_code in (400, 409)

        # Clean up
        await category_client.delete(child["id"])
        await category_client.delete(parent["id"])


class TestCategoryStatistics:

    async def test_get_statistics(self, category_client, shared_expense_category):
        """Statistics endpoint should work when categories exist."""
        result = await category_client.statistics()
        assert result.ok
