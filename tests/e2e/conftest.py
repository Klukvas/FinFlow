"""Root conftest for E2E API tests.

Session-scoped fixtures create shared test users and workspaces.
Function-scoped fixtures provide fresh API client instances per test.
"""
from __future__ import annotations

import asyncio
import pytest

import base64
import json
import os

from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.clients.workspace_client import WorkspaceApiClient
from tests.e2e.clients.category_client import CategoryApiClient
from tests.e2e.clients.expense_client import ExpenseApiClient
from tests.e2e.clients.income_client import IncomeApiClient
from tests.e2e.clients.account_client import AccountApiClient
from tests.e2e.clients.subscription_client import SubscriptionApiClient
from tests.e2e.clients.ai_assistant_client import AiAssistantApiClient
from tests.e2e.clients.debt_client import DebtApiClient
from tests.e2e.clients.goals_client import GoalsApiClient
from tests.e2e.clients.recurring_client import RecurringApiClient
from tests.e2e.clients.currency_client import CurrencyApiClient
from tests.e2e.clients.pdf_parser_client import PdfParserApiClient
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
def debt_client(primary_user, workspace_id) -> DebtApiClient:
    client = DebtApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def goals_client(primary_user, workspace_id) -> GoalsApiClient:
    client = GoalsApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def recurring_client(primary_user, workspace_id) -> RecurringApiClient:
    client = RecurringApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


@pytest.fixture
def currency_client() -> CurrencyApiClient:
    """Currency service doesn't require auth for public endpoints."""
    return CurrencyApiClient()


@pytest.fixture
def pdf_parser_client(primary_user) -> PdfParserApiClient:
    client = PdfParserApiClient()
    client.set_token(primary_user["token"])
    return client


@pytest.fixture
def unauthenticated_pdf_client() -> PdfParserApiClient:
    """PDF parser client without auth token for negative auth tests."""
    return PdfParserApiClient()


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


# ---------------------------------------------------------------------------
# AI Assistant: basic-plan client (uses primary_user)
# ---------------------------------------------------------------------------

@pytest.fixture
def ai_assistant_client(primary_user, workspace_id) -> AiAssistantApiClient:
    client = AiAssistantApiClient()
    client.set_token(primary_user["token"])
    client.set_workspace_id(workspace_id)
    return client


# ---------------------------------------------------------------------------
# Session-scoped: professional-plan user for AI assistant tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def professional_user():
    """Register a user and upgrade to professional plan."""
    email = unique_email()
    password = strong_password()
    user_client = UserApiClient()
    result = await user_client.register(email, password)
    data = result.raise_on_error()

    token = data["access_token"]

    # Decode JWT to extract user_id (registration response doesn't include it)
    payload_b64 = token.split(".")[1]
    payload_b64 += "==" * (4 - len(payload_b64) % 4)
    jwt_payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    user_id = jwt_payload["sub"]

    internal_token = os.environ.get("INTERNAL_SECRET_TOKEN")
    assert internal_token, "INTERNAL_SECRET_TOKEN env var must be set for AI assistant tests"
    sub_client = SubscriptionApiClient()
    result = await sub_client.set_plan(user_id, "professional", internal_token=internal_token)
    result.raise_on_error()

    return {
        "email": email,
        "password": password,
        "token": token,
        "user_id": user_id,
    }


@pytest.fixture(scope="session")
async def professional_workspace(professional_user):
    """Get auto-created workspace for the professional user."""
    client = WorkspaceApiClient()
    client.set_token(professional_user["token"])
    result = await client.list_all()
    data = result.raise_on_error()
    workspaces = data.get("workspaces", data) if isinstance(data, dict) else data
    assert len(workspaces) >= 1, "Expected at least one workspace"
    return workspaces[0]


@pytest.fixture(scope="session")
def professional_workspace_id(professional_workspace) -> str:
    return str(professional_workspace["id"])


@pytest.fixture
def pro_ai_client(professional_user, professional_workspace_id) -> AiAssistantApiClient:
    client = AiAssistantApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    return client


# ---------------------------------------------------------------------------
# Pro-plan shared categories & account (for debt/goals/recurring tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def pro_shared_expense_category(professional_user, professional_workspace_id):
    """Shared expense category in the professional workspace."""
    client = CategoryApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    result = await client.create("Pro E2E Expense Cat")
    return result.raise_on_error()


@pytest.fixture(scope="session")
async def pro_shared_income_category(professional_user, professional_workspace_id):
    """Shared income category in the professional workspace."""
    client = CategoryApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    result = await client.create("Pro E2E Income Cat", cat_type="INCOME")
    return result.raise_on_error()


@pytest.fixture(scope="session")
async def pro_shared_account(professional_user, professional_workspace_id):
    """Shared account in the professional workspace."""
    client = AccountApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    result = await client.create("Pro E2E Account", balance=5000.0)
    return result.raise_on_error()


# ---------------------------------------------------------------------------
# Pro-plan service clients (for debt/goals/recurring that need higher limits)
# ---------------------------------------------------------------------------

@pytest.fixture
def pro_debt_client(professional_user, professional_workspace_id) -> DebtApiClient:
    client = DebtApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    return client


@pytest.fixture
def pro_goals_client(professional_user, professional_workspace_id) -> GoalsApiClient:
    client = GoalsApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    return client


@pytest.fixture
def pro_recurring_client(professional_user, professional_workspace_id) -> RecurringApiClient:
    client = RecurringApiClient()
    client.set_token(professional_user["token"])
    client.set_workspace_id(professional_workspace_id)
    return client
