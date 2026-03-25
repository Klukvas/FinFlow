"""
Unit tests for Internal API Routers.

Tests cover:
- GET /internal/debts/ai-summary - AI summary endpoint
- Authentication and error handling
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date
from uuid import uuid4

from app.models.debt import Debt


class TestGetDebtsAiSummary:
    """Tests for GET /internal/debts/ai-summary"""

    def test_ai_summary_success(self, client, db_session):
        """Successfully get AI summary with active debts."""
        ws_id = client.workspace_id

        debt1 = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="Credit Card",
            debt_type="CREDIT_CARD",
            currency="USD",
            initial_amount=Decimal("5000.00"),
            current_balance=Decimal("4500.00"),
            interest_rate=Decimal("18.99"),
            minimum_payment=Decimal("150.00"),
            start_date=date(2024, 1, 1),
            due_date=date(2025, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        debt2 = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="Student Loan",
            debt_type="STUDENT_LOAN",
            currency="USD",
            initial_amount=Decimal("20000.00"),
            current_balance=Decimal("18000.00"),
            interest_rate=Decimal("4.50"),
            start_date=date(2023, 6, 1),
            is_active=True,
            is_paid_off=False,
        )
        db_session.add_all([debt1, debt2])
        db_session.commit()

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2

        # Verify item structure
        item = data["items"][0]
        assert "name" in item
        assert "debt_type" in item
        assert "current_balance" in item
        assert "interest_rate" in item
        assert "due_date" in item
        assert "minimum_payment" in item
        assert "currency" in item

    def test_ai_summary_empty(self, client):
        """Return empty items when no debts."""
        ws_id = client.workspace_id

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_ai_summary_excludes_inactive(self, client, db_session):
        """Only active debts are included in AI summary."""
        ws_id = client.workspace_id

        active_debt = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="Active Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("1000.00"),
            current_balance=Decimal("800.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        inactive_debt = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="Inactive Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("2000.00"),
            current_balance=Decimal("0.00"),
            start_date=date(2023, 1, 1),
            is_active=False,
            is_paid_off=True,
        )
        db_session.add_all([active_debt, inactive_debt])
        db_session.commit()

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Active Debt"

    def test_ai_summary_handles_null_optional_fields(self, client, db_session):
        """Handle debts with null optional fields."""
        ws_id = client.workspace_id

        debt = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="Minimal Debt",
            debt_type="OTHER",
            currency="EUR",
            initial_amount=Decimal("500.00"),
            current_balance=Decimal("500.00"),
            interest_rate=None,
            minimum_payment=None,
            due_date=None,
            start_date=date(2024, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        db_session.add(debt)
        db_session.commit()

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        item = response.json()["items"][0]
        assert item["interest_rate"] is None
        assert item["minimum_payment"] is None
        assert item["due_date"] is None

    def test_ai_summary_invalid_user_id(self, client):
        """Reject invalid user_id parameter."""
        ws_id = client.workspace_id

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 0, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 422

    def test_ai_summary_missing_user_id(self, client):
        """Reject missing user_id parameter."""
        ws_id = client.workspace_id

        response = client.get(
            "/internal/debts/ai-summary",
            params={"workspace_id": str(ws_id)},
        )

        assert response.status_code == 422

    def test_ai_summary_missing_workspace_id(self, client):
        """Reject missing workspace_id parameter."""
        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1},
        )

        assert response.status_code == 422

    def test_ai_summary_isolates_users(self, client, db_session):
        """Only return debts for the specified user."""
        ws_id = client.workspace_id

        user1_debt = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="User 1 Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        user2_debt = Debt(
            user_id=2,
            workspace_id=ws_id,
            name="User 2 Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("2000.00"),
            current_balance=Decimal("2000.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add_all([user1_debt, user2_debt])
        db_session.commit()

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "User 1 Debt"

    def test_ai_summary_isolates_workspaces(self, client, db_session):
        """Only return debts for the specified workspace."""
        ws_id = client.workspace_id
        other_ws = uuid4()

        ws_debt = Debt(
            user_id=1,
            workspace_id=ws_id,
            name="This WS Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        other_debt = Debt(
            user_id=1,
            workspace_id=other_ws,
            name="Other WS Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("2000.00"),
            current_balance=Decimal("2000.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add_all([ws_debt, other_debt])
        db_session.commit()

        response = client.get(
            "/internal/debts/ai-summary",
            params={"user_id": 1, "workspace_id": str(ws_id)},
        )

        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "This WS Debt"
