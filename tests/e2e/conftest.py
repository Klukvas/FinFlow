"""Root conftest for E2E API tests.

Session-scoped fixtures create shared test users and workspaces.
Function-scoped fixtures provide fresh API client instances per test.
"""
from __future__ import annotations

import asyncio
import pytest

from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.clients.workspace_client import WorkspaceApiClient
from tests.e2e.clients.category_client import CategoryApiClient
from tests.e2e.clients.expense_client import ExpenseApiClient
from tests.e2e.clients.income_client import IncomeApiClient
from tests.e2e.clients.account_client import AccountApiClient
from tests.e2e.clients.subscription_client import SubscriptionApiClient
from tests.e2e.helpers.test_data import unique_email, strong_password, workspace_name
from tests.e2e.helpers.wait import wait_for_services


# ---------------------------------------------------------------------------
# Session-scoped: wait for all services
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Override default event loop to be session-scoped."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def ensure_services_ready():
    """Block until all docker-compose services are healthy."""
    await wait_for_services(max_wait=120.0)


# ---------------------------------------------------------------------------
# Session-scoped: primary test user
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def primary_user():
    """Register a primary test user. Returns (email, password, token, user_id)."""
    email = unique_email()
    password = strong_password()
    client = UserApiClient()
    result = await client.register(email, password)
    data = result.raise_on_error()
    return {
        "email": email,
        "password": password,
        "token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "user_id": data.get("user_id") or data.get("id"),
    }


@pytest.fixture(scope="session")
async def secondary_user():
    """Register a secondary test user for multi-user scenarios."""
    email = unique_email()
    password = strong_password()
    client = UserApiClient()
    result = await client.register(email, password)
    data = result.raise_on_error()
    return {
        "email": email,
        "password": password,
        "token": data["access_token"],
        "user_id": data.get("user_id") or data.get("id"),
    }


# ---------------------------------------------------------------------------
# Session-scoped: workspace
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def shared_workspace(primary_user):
    """Use the auto-created personal workspace (basic plan limits to 1)."""
    client = WorkspaceApiClient()
    client.set_token(primary_user["token"])
    result = await client.list_all()
    data = result.raise_on_error()
    workspaces = data.get("workspaces", data) if isinstance(data, dict) else data
    assert len(workspaces) >= 1, "Expected at least one workspace after registration"
    return workspaces[0]


@pytest.fixture(scope="session")
def workspace_id(shared_workspace) -> str:
    """Extract workspace ID as string."""
    return str(shared_workspace["id"])


# ---------------------------------------------------------------------------
# Function-scoped: fresh API clients with auth pre-configured
# ---------------------------------------------------------------------------

@pytest.fixture
def user_client(primary_user) -> UserApiClient:
    client = UserApiClient()
    client.set_token(primary_user["token"])
    return client


@pytest.fixture
def workspace_client(primary_user, workspace_id) -> WorkspaceApiClient:
    client = WorkspaceApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def category_client(primary_user, workspace_id) -> CategoryApiClient:
    client = CategoryApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def expense_client(primary_user, workspace_id) -> ExpenseApiClient:
    client = ExpenseApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def income_client(primary_user, workspace_id) -> IncomeApiClient:
    client = IncomeApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def account_client(primary_user, workspace_id) -> AccountApiClient:
    client = AccountApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


# ---------------------------------------------------------------------------
# Session-scoped: shared categories and account (plan limits are strict)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def shared_expense_category(primary_user, workspace_id):
    """Shared expense category — reuse across tests to stay within limits."""
    client = CategoryApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    result = await client.create("E2E Shared Expense Cat")
    return result.raise_on_error()


@pytest.fixture(scope="session")
async def shared_income_category(primary_user, workspace_id):
    """Shared income category — reuse across tests to stay within limits."""
    client = CategoryApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    result = await client.create("E2E Shared Income Cat", cat_type="INCOME")
    return result.raise_on_error()


@pytest.fixture(scope="session")
async def shared_account(primary_user, workspace_id):
    """Shared account — reuse across tests to stay within limits."""
    client = AccountApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    result = await client.create("E2E Shared Account", balance=1000.0)
    return result.raise_on_error()


@pytest.fixture
def subscription_client(primary_user) -> SubscriptionApiClient:
    client = SubscriptionApiClient()
    client.set_token(primary_user["token"])
    return client


# ---------------------------------------------------------------------------
# Secondary user clients
# ---------------------------------------------------------------------------

@pytest.fixture
def secondary_user_client(secondary_user) -> UserApiClient:
    client = UserApiClient()
    client.set_token(secondary_user["token"])
    return client


@pytest.fixture
def secondary_workspace_client(secondary_user, workspace_id) -> WorkspaceApiClient:
    client = WorkspaceApiClient()
    client.set_token(secondary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def secondary_expense_client(secondary_user, workspace_id) -> ExpenseApiClient:
    client = ExpenseApiClient()
    client.set_token(secondary_user["token"])
    client.set_workspace_id(workspace_id)
    return client
