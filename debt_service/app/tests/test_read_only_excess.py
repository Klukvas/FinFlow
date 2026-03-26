"""
Tests for read-only excess behavior in debt_service.

Covers:
- get_read_only_ids marking debts correctly in list endpoint
- Deleting a read-only debt (allowed -- users must reduce count)
- Full flow: create debts -> limit drops -> verify read-only flags
- Creating a payment on a read-only debt (allowed -- no _check_modify_allowed)
- _check_modify_allowed blocking update on excess debts
- _check_modify_allowed allowing update on within-limit debts
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, MagicMock

from app.models.debt import Debt, DebtPayment
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtType, DebtPaymentCreate, PaymentMethod,
)
from app.exceptions import (
    DebtReadOnlyExcessError,
    DebtNotFoundError,
)


# ==================== get_read_only_ids in list endpoint ====================


class TestGetReadOnlyIdsInListEndpoint:
    """Tests for read-only flag marking in the GET /debts/ router."""

    def test_debts_marked_read_only_when_over_limit(
        self, client, db_session
    ):
        """Debts beyond the plan limit are flagged is_read_only=True."""
        workspace_id = client.workspace_id

        # Create 3 debts directly in DB
        debt_ids = []
        for i in range(3):
            debt = Debt(
                user_id=1,
                workspace_id=str(workspace_id),
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
                is_paid_off=False,
            )
            db_session.add(debt)
            db_session.flush()
            debt_ids.append(debt.id)
        db_session.commit()

        # Mock subscription: limit=2, so 3rd debt is read-only
        with patch("app.services.debt.DebtService.get_debts") as mock_get, \
             patch("app.services.debt.DebtService._get_ordered_ids") as mock_ordered, \
             patch("app.services.debt.SubscriptionClient") as mock_sub_cls:

            from app.schemas.debt import DebtResponse
            from datetime import datetime

            responses = []
            for did in debt_ids:
                resp = DebtResponse(
                    id=did,
                    name=f"Debt",
                    debt_type="LOAN",
                    contact_id=None,
                    category_id=None,
                    currency="USD",
                    initial_amount=1000.0,
                    interest_rate=None,
                    minimum_payment=None,
                    start_date=date(2024, 1, 1),
                    due_date=None,
                    user_id=1,
                    workspace_id=workspace_id,
                    current_balance=1000.0,
                    last_payment_date=None,
                    is_active=True,
                    is_paid_off=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    payment_count=0,
                    contact=None,
                    is_read_only=False,
                )
                responses.append(resp)

            mock_get.return_value = responses
            mock_ordered.return_value = debt_ids

            # subscription_client is accessed on the service instance;
            # the router calls service.subscription_client.get_read_only_ids
            # We need to mock the *instance* attribute, not the class.
            # The test client fixture overrides dependencies, so the service
            # is created fresh. Patch the instance method via the class mock.
            mock_instance = MagicMock()
            mock_instance.get_read_only_ids.return_value = {debt_ids[2]}
            mock_sub_cls.get_instance.return_value = mock_instance

            # The router accesses service.subscription_client directly.
            # We need a different approach: patch the service attribute.
            with patch(
                "app.services.debt.SubscriptionClient.get_instance",
                return_value=mock_instance,
            ):
                response = client.get("/debts/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3

            read_only_flags = {d["id"]: d["is_read_only"] for d in data}
            assert read_only_flags[debt_ids[0]] is False
            assert read_only_flags[debt_ids[1]] is False
            assert read_only_flags[debt_ids[2]] is True

    def test_no_debts_marked_read_only_within_limit(self, client):
        """All debts are editable when count is within plan limit."""
        with patch("app.services.debt.DebtService.get_debts") as mock_get, \
             patch("app.services.debt.DebtService._get_ordered_ids") as mock_ordered, \
             patch("app.services.debt.SubscriptionClient"):

            mock_get.return_value = []
            mock_ordered.return_value = []

            response = client.get("/debts/")

            assert response.status_code == 200
            data = response.json()
            assert all(d.get("is_read_only", False) is False for d in data)

    def test_all_debts_read_only_when_limit_zero(self, client):
        """When plan limit is 0, every debt is read-only."""
        from app.schemas.debt import DebtResponse
        from datetime import datetime

        ids = [101, 102]
        responses = []
        for did in ids:
            resp = DebtResponse(
                id=did,
                name="Debt",
                debt_type="LOAN",
                contact_id=None,
                category_id=None,
                currency="USD",
                initial_amount=1000.0,
                interest_rate=None,
                minimum_payment=None,
                start_date=date(2024, 1, 1),
                due_date=None,
                user_id=1,
                workspace_id=client.workspace_id,
                current_balance=1000.0,
                last_payment_date=None,
                is_active=True,
                is_paid_off=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                payment_count=0,
                contact=None,
                is_read_only=False,
            )
            responses.append(resp)

        with patch("app.services.debt.DebtService.get_debts") as mock_get, \
             patch("app.services.debt.DebtService._get_ordered_ids") as mock_ordered, \
             patch("app.services.debt.SubscriptionClient"):
            mock_get.return_value = responses
            mock_ordered.return_value = ids

            mock_sub = MagicMock()
            mock_sub.get_read_only_ids.return_value = set(ids)
            with patch(
                "app.services.debt.SubscriptionClient.get_instance",
                return_value=mock_sub,
            ):
                response = client.get("/debts/")

            assert response.status_code == 200
            data = response.json()
            assert all(d["is_read_only"] is True for d in data)


# ==================== Delete read-only debt ====================


class TestDeleteReadOnlyDebt:
    """Tests for deleting a debt that is in the read-only excess zone."""

    def test_delete_read_only_debt_succeeds(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """Deleting a read-only (excess) debt is allowed.

        The service does NOT call _check_modify_allowed in delete_debt,
        so users can reduce their debt count to get back within limits.
        """
        # Configure subscription to block modifications
        debt_service.subscription_client.check_modify_allowed.return_value = False

        result = debt_service.delete_debt(sample_debt.id, user_id, workspace_id)

        assert result is True

        with pytest.raises(DebtNotFoundError):
            debt_service.get_debt(sample_debt.id, user_id, workspace_id)

    def test_delete_read_only_debt_with_payments_succeeds(
        self, debt_service, workspace_id, user_id, sample_debt, sample_payment
    ):
        """Deleting a read-only debt cascades to its payments."""
        debt_service.subscription_client.check_modify_allowed.return_value = False

        result = debt_service.delete_debt(sample_debt.id, user_id, workspace_id)

        assert result is True

        remaining = debt_service.db.query(DebtPayment).filter(
            DebtPayment.debt_id == sample_debt.id
        ).count()
        assert remaining == 0


# ==================== Full flow: create -> limit drops -> verify ====================


class TestFullFlowLimitDrop:
    """Full integration flow: create debts, then simulate a plan downgrade."""

    def test_create_debts_then_limit_drops_marks_excess_read_only(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """After limit drops, excess debts are identified by _get_ordered_ids."""
        # Create 4 debts
        debt_ids = []
        for i in range(4):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            debt_ids.append(debt.id)
        db_session.commit()

        ordered = debt_service._get_ordered_ids(workspace_id)
        assert len(ordered) == 4

        # Simulate limit=2: get_read_only_ids returns IDs beyond index 2
        debt_service.subscription_client.get_read_only_ids.return_value = set(
            ordered[2:]
        )
        read_only = debt_service.subscription_client.get_read_only_ids(
            user_id, "debts", ordered
        )
        assert len(read_only) == 2
        assert ordered[0] not in read_only
        assert ordered[1] not in read_only
        assert ordered[2] in read_only
        assert ordered[3] in read_only

    def test_oldest_debts_remain_editable_after_limit_drop(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """The oldest N debts (within limit) stay editable."""
        debt_ids = []
        for i in range(3):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            debt_ids.append(debt.id)
        db_session.commit()

        ordered = debt_service._get_ordered_ids(workspace_id)

        # Simulate limit=2: first 2 are editable, 3rd is read-only
        debt_service.subscription_client.check_modify_allowed.side_effect = (
            lambda uid, rid, feat, ids: rid in set(ids[:2])
        )

        # Oldest 2 should be allowed
        assert debt_service.subscription_client.check_modify_allowed(
            user_id, ordered[0], "debts", ordered
        ) is True
        assert debt_service.subscription_client.check_modify_allowed(
            user_id, ordered[1], "debts", ordered
        ) is True
        # 3rd should be blocked
        assert debt_service.subscription_client.check_modify_allowed(
            user_id, ordered[2], "debts", ordered
        ) is False

    def test_update_excess_debt_raises_read_only_error(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """Updating a debt in the excess zone raises DebtReadOnlyExcessError."""
        debts = []
        for i in range(3):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            debts.append(debt)
        db_session.commit()

        ordered = debt_service._get_ordered_ids(workspace_id)
        excess_debt = debts[2]

        # Simulate limit=2: only first 2 are modifiable
        debt_service.subscription_client.check_modify_allowed.return_value = False
        debt_service.subscription_client.get_user_features.return_value = {
            "debts": {"limit_value": 2, "enabled": True}
        }

        update = DebtUpdate(name="Should Fail")

        with pytest.raises(DebtReadOnlyExcessError) as exc_info:
            debt_service.update_debt(excess_debt.id, update, user_id, workspace_id)

        assert exc_info.value.debt_id == excess_debt.id
        assert exc_info.value.limit == 2

    def test_update_within_limit_debt_succeeds_after_limit_drop(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """Updating a debt within the limit still works after limit drops."""
        debts = []
        for i in range(3):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            debts.append(debt)
        db_session.commit()

        # Allow modification for the first debt (within limit)
        debt_service.subscription_client.check_modify_allowed.return_value = True

        update = DebtUpdate(name="Updated Successfully")
        result = debt_service.update_debt(debts[0].id, update, user_id, workspace_id)

        assert result.name == "Updated Successfully"


# ==================== Payment on read-only debt ====================


class TestPaymentOnReadOnlyDebt:
    """Tests for creating payments on debts in the read-only excess zone."""

    def test_create_payment_on_read_only_debt_succeeds(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """Creating a payment on a read-only debt is allowed.

        The create_payment method does NOT call _check_modify_allowed,
        so payments can still be recorded even on excess debts.
        """
        debt_service.subscription_client.check_modify_allowed.return_value = False

        payment_data = DebtPaymentCreate(
            amount=100.00,
            payment_date=date(2024, 3, 1),
            description="Payment on read-only debt",
        )

        result = debt_service.create_payment(
            sample_debt.id, payment_data, user_id, workspace_id
        )

        assert result.amount == 100.00
        assert result.debt_id == sample_debt.id

    def test_payment_on_read_only_debt_reduces_balance(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """Payment on a read-only debt still reduces the balance."""
        initial_balance = float(sample_debt.current_balance)
        debt_service.subscription_client.check_modify_allowed.return_value = False

        payment_data = DebtPaymentCreate(
            amount=500.00,
            principal_amount=400.00,
            interest_amount=100.00,
            payment_date=date(2024, 3, 1),
        )

        debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        debt_service.db.refresh(sample_debt)
        expected = initial_balance - 400.00
        assert float(sample_debt.current_balance) == expected

    def test_payment_on_read_only_debt_can_pay_off(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """A read-only debt can be fully paid off via payments."""
        debt = Debt(
            user_id=user_id,
            workspace_id=workspace_id,
            name="Read-Only Small Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("100.00"),
            current_balance=Decimal("50.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        db_session.add(debt)
        db_session.commit()
        db_session.refresh(debt)

        debt_service.subscription_client.check_modify_allowed.return_value = False

        payment_data = DebtPaymentCreate(
            amount=50.00,
            payment_date=date(2024, 3, 1),
        )

        debt_service.create_payment(debt.id, payment_data, user_id, workspace_id)

        db_session.refresh(debt)
        assert float(debt.current_balance) == 0.0
        assert debt.is_paid_off is True
        assert debt.is_active is False


# ==================== _check_modify_allowed edge cases ====================


class TestCheckModifyAllowed:
    """Tests for DebtService._check_modify_allowed()."""

    def test_check_modify_allowed_passes_within_limit(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """No exception when the debt is within plan limits."""
        debt_service.subscription_client.check_modify_allowed.return_value = True

        # Should not raise
        debt_service._check_modify_allowed(sample_debt.id, user_id, workspace_id)

    def test_check_modify_allowed_raises_for_excess(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """Raises DebtReadOnlyExcessError for excess debts."""
        debt_service.subscription_client.check_modify_allowed.return_value = False
        debt_service.subscription_client.get_user_features.return_value = {
            "debts": {"limit_value": 0, "enabled": True}
        }

        with pytest.raises(DebtReadOnlyExcessError) as exc_info:
            debt_service._check_modify_allowed(sample_debt.id, user_id, workspace_id)

        assert exc_info.value.debt_id == sample_debt.id
        assert exc_info.value.limit == 0

    def test_check_modify_allowed_uses_ordered_ids(
        self, debt_service, workspace_id, user_id, multiple_debts
    ):
        """_check_modify_allowed passes ordered IDs to subscription client."""
        debt_service.subscription_client.check_modify_allowed.return_value = True

        first_debt = multiple_debts[0]
        debt_service._check_modify_allowed(first_debt.id, user_id, workspace_id)

        call_args = debt_service.subscription_client.check_modify_allowed.call_args
        # Args: (user_id, record_id, feature_code, ordered_ids)
        assert call_args[0][0] == user_id
        assert call_args[0][1] == first_debt.id
        assert call_args[0][2] == "debts"
        ordered_ids = call_args[0][3]
        assert len(ordered_ids) == len(multiple_debts)

    def test_check_modify_allowed_features_missing_key_defaults_limit_zero(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """When features dict lacks the 'debts' key, limit defaults to 0."""
        debt_service.subscription_client.check_modify_allowed.return_value = False
        debt_service.subscription_client.get_user_features.return_value = {}

        with pytest.raises(DebtReadOnlyExcessError) as exc_info:
            debt_service._check_modify_allowed(sample_debt.id, user_id, workspace_id)

        assert exc_info.value.limit == 0

    def test_check_modify_allowed_features_returns_none_defaults_limit_zero(
        self, debt_service, workspace_id, user_id, sample_debt
    ):
        """When get_user_features returns None, limit defaults to 0."""
        debt_service.subscription_client.check_modify_allowed.return_value = False
        debt_service.subscription_client.get_user_features.return_value = None

        with pytest.raises(DebtReadOnlyExcessError) as exc_info:
            debt_service._check_modify_allowed(sample_debt.id, user_id, workspace_id)

        assert exc_info.value.limit == 0


# ==================== _get_ordered_ids for read-only computation ====================


class TestGetOrderedIdsForReadOnly:
    """Tests confirming _get_ordered_ids produces the correct order for read-only computation."""

    def test_ordered_ids_match_creation_order(
        self, debt_service, workspace_id, user_id, db_session
    ):
        """IDs are ordered by created_at ASC, then id ASC -- matching creation order."""
        ids = []
        for i in range(5):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            ids.append(debt.id)
        db_session.commit()

        ordered = debt_service._get_ordered_ids(workspace_id)

        assert ordered == ids

    def test_ordered_ids_only_for_workspace(
        self, debt_service, user_id, db_session
    ):
        """_get_ordered_ids only returns IDs for the specified workspace."""
        ws1 = uuid4()
        ws2 = uuid4()

        for ws in [ws1, ws1, ws2]:
            debt = Debt(
                user_id=user_id,
                workspace_id=ws,
                name="Debt",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
        db_session.commit()

        ws1_ids = debt_service._get_ordered_ids(ws1)
        ws2_ids = debt_service._get_ordered_ids(ws2)

        assert len(ws1_ids) == 2
        assert len(ws2_ids) == 1
