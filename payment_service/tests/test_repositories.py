"""Tests for PaymentRepository and PaymentEventRepository.

Uses the mock_db fixture from conftest.py to verify query construction,
status transition validation, and error handling.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4, UUID

from payment_service.app.models.models import (
    Payment,
    PaymentEvent,
    PaymentEventType,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
)
from payment_service.app.repositories.payment_repository import (
    PaymentRepository,
    VALID_TRANSITIONS,
)
from payment_service.app.repositories.payment_event_repository import (
    PaymentEventRepository,
)
from payment_service.app.utils.errors import NotFoundError


# ======================================================================
# PaymentRepository
# ======================================================================


class TestPaymentRepositoryCreate:
    """Tests for PaymentRepository.create."""

    def test_adds_and_commits_payment(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.order_reference = "ORDER_test"
        payment.amount = Decimal("10.00")
        payment.status = PaymentStatus.CREATED

        repo.create(payment)

        mock_db.add.assert_called_once_with(payment)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(payment)

    def test_returns_the_payment(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.order_reference = "ORDER_ret"
        payment.amount = Decimal("5.00")
        payment.status = PaymentStatus.CREATED

        result = repo.create(payment)
        assert result is payment


class TestPaymentRepositoryGetById:
    """Tests for PaymentRepository.get_by_id."""

    def test_returns_payment_when_found(self, mock_db):
        payment_id = uuid4()
        mock_payment = MagicMock(spec=Payment)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_payment
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_by_id(payment_id)
        assert result is mock_payment

    def test_returns_none_when_not_found(self, mock_db):
        repo = PaymentRepository(mock_db)
        result = repo.get_by_id(uuid4())
        assert result is None


class TestPaymentRepositoryGetByIdOrRaise:
    """Tests for PaymentRepository.get_by_id_or_raise."""

    def test_returns_payment_when_found(self, mock_db):
        payment_id = uuid4()
        mock_payment = MagicMock(spec=Payment)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_payment
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_by_id_or_raise(payment_id)
        assert result is mock_payment

    def test_raises_not_found_error_when_missing(self, mock_db):
        repo = PaymentRepository(mock_db)
        with pytest.raises(NotFoundError) as exc_info:
            repo.get_by_id_or_raise(uuid4())
        assert "PAYMENT_NOT_FOUND" in exc_info.value.error_code


class TestPaymentRepositoryGetByOrderReference:
    """Tests for PaymentRepository.get_by_order_reference."""

    def test_returns_payment_when_found(self, mock_db):
        mock_payment = MagicMock(spec=Payment)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_payment
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_by_order_reference("ORDER_123")
        assert result is mock_payment

    def test_returns_none_when_not_found(self, mock_db):
        repo = PaymentRepository(mock_db)
        result = repo.get_by_order_reference("ORDER_MISSING")
        assert result is None


class TestPaymentRepositoryGetByOrderReferenceOrRaise:
    """Tests for PaymentRepository.get_by_order_reference_or_raise."""

    def test_raises_not_found_error_when_missing(self, mock_db):
        repo = PaymentRepository(mock_db)
        with pytest.raises(NotFoundError) as exc_info:
            repo.get_by_order_reference_or_raise("ORDER_NONEXISTENT")
        assert "PAYMENT_NOT_FOUND" in exc_info.value.error_code


class TestPaymentRepositoryGetByUserId:
    """Tests for PaymentRepository.get_by_user_id."""

    def test_returns_list_of_payments(self, mock_db):
        payments = [MagicMock(spec=Payment), MagicMock(spec=Payment)]
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.all.return_value = payments
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_by_user_id("user_1")
        assert len(result) == 2

    def test_returns_empty_list_when_none(self, mock_db):
        repo = PaymentRepository(mock_db)
        result = repo.get_by_user_id("user_missing")
        assert result == []


class TestPaymentRepositoryGetByWorkspaceId:
    """Tests for PaymentRepository.get_by_workspace_id."""

    def test_returns_list_of_payments(self, mock_db):
        payments = [MagicMock(spec=Payment)]
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.all.return_value = payments
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_by_workspace_id("ws_1")
        assert len(result) == 1


class TestPaymentRepositoryUpdateStatus:
    """Tests for PaymentRepository.update_status with transition validation."""

    def _make_payment(self, current_status: PaymentStatus) -> MagicMock:
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.order_reference = "ORDER_status_test"
        payment.status = current_status
        payment.paid_at = None
        payment.failed_at = None
        payment.refunded_at = None
        payment.failure_reason = None
        payment.updated_at = None
        return payment

    def test_valid_transition_created_to_paid(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CREATED)

        result = repo.update_status(payment, PaymentStatus.PAID)

        assert payment.status == PaymentStatus.PAID
        assert payment.paid_at is not None
        mock_db.commit.assert_called()

    def test_valid_transition_created_to_failed(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CREATED)

        repo.update_status(payment, PaymentStatus.FAILED, reason="card_declined")

        assert payment.status == PaymentStatus.FAILED
        assert payment.failed_at is not None
        assert payment.failure_reason == "card_declined"

    def test_valid_transition_created_to_canceled(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CREATED)

        repo.update_status(payment, PaymentStatus.CANCELED)
        assert payment.status == PaymentStatus.CANCELED
        assert payment.failed_at is not None

    def test_valid_transition_created_to_expired(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CREATED)

        repo.update_status(payment, PaymentStatus.EXPIRED)
        assert payment.status == PaymentStatus.EXPIRED

    def test_valid_transition_paid_to_refunded(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.PAID)

        repo.update_status(payment, PaymentStatus.REFUNDED)

        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_at is not None

    def test_valid_transition_paid_to_partially_refunded(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.PAID)

        repo.update_status(payment, PaymentStatus.PARTIALLY_REFUNDED)

        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert payment.refunded_at is not None

    def test_valid_transition_partially_refunded_to_refunded(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.PARTIALLY_REFUNDED)

        repo.update_status(payment, PaymentStatus.REFUNDED)
        assert payment.status == PaymentStatus.REFUNDED

    def test_invalid_transition_paid_to_created_raises(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.PAID)

        with pytest.raises(ValueError, match="Invalid status transition"):
            repo.update_status(payment, PaymentStatus.CREATED)

    def test_invalid_transition_failed_to_paid_raises(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.FAILED)

        with pytest.raises(ValueError, match="Invalid status transition"):
            repo.update_status(payment, PaymentStatus.PAID)

    def test_invalid_transition_refunded_to_paid_raises(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.REFUNDED)

        with pytest.raises(ValueError, match="Invalid status transition"):
            repo.update_status(payment, PaymentStatus.PAID)

    def test_invalid_transition_canceled_to_anything_raises(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CANCELED)

        with pytest.raises(ValueError, match="Invalid status transition"):
            repo.update_status(payment, PaymentStatus.PAID)

    def test_invalid_transition_expired_to_anything_raises(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.EXPIRED)

        with pytest.raises(ValueError, match="Invalid status transition"):
            repo.update_status(payment, PaymentStatus.PENDING)

    def test_no_reason_on_failed_status_leaves_failure_reason_none(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = self._make_payment(PaymentStatus.CREATED)

        repo.update_status(payment, PaymentStatus.FAILED)
        assert payment.failure_reason is None


class TestPaymentRepositoryUpdate:
    """Tests for PaymentRepository.update."""

    def test_commits_and_refreshes(self, mock_db):
        repo = PaymentRepository(mock_db)
        payment = MagicMock(spec=Payment)

        repo.update(payment)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(payment)
        assert payment.updated_at is not None


class TestPaymentRepositoryGetActivePaymentForUserPlan:
    """Tests for PaymentRepository.get_active_payment_for_user_plan."""

    def test_returns_payment_when_found(self, mock_db):
        mock_payment = MagicMock(spec=Payment)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_payment
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.get_active_payment_for_user_plan("user_1", "professional")
        assert result is mock_payment

    def test_returns_none_when_not_found(self, mock_db):
        repo = PaymentRepository(mock_db)
        result = repo.get_active_payment_for_user_plan("user_1", "nonexistent")
        assert result is None


class TestPaymentRepositoryCountByStatus:
    """Tests for PaymentRepository.count_by_status."""

    def test_returns_count(self, mock_db):
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 42
        mock_db.query.return_value = query_mock

        repo = PaymentRepository(mock_db)
        result = repo.count_by_status(PaymentStatus.PAID)
        assert result == 42


class TestValidTransitions:
    """Tests for the VALID_TRANSITIONS mapping."""

    def test_created_allows_pending_paid_failed_canceled_expired(self):
        allowed = VALID_TRANSITIONS[PaymentStatus.CREATED]
        expected = {
            PaymentStatus.PENDING,
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELED,
            PaymentStatus.EXPIRED,
        }
        assert allowed == expected

    def test_pending_allows_paid_failed_canceled_expired(self):
        allowed = VALID_TRANSITIONS[PaymentStatus.PENDING]
        expected = {
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELED,
            PaymentStatus.EXPIRED,
        }
        assert allowed == expected

    def test_paid_allows_refunded_and_partially_refunded(self):
        allowed = VALID_TRANSITIONS[PaymentStatus.PAID]
        assert allowed == {PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED}

    def test_terminal_states_allow_nothing(self):
        for terminal in (PaymentStatus.FAILED, PaymentStatus.CANCELED, PaymentStatus.EXPIRED, PaymentStatus.REFUNDED):
            assert VALID_TRANSITIONS[terminal] == set()

    def test_partially_refunded_allows_refunded(self):
        allowed = VALID_TRANSITIONS[PaymentStatus.PARTIALLY_REFUNDED]
        assert allowed == {PaymentStatus.REFUNDED}


# ======================================================================
# PaymentEventRepository
# ======================================================================


class TestPaymentEventRepositoryCreate:
    """Tests for PaymentEventRepository.create."""

    def test_adds_and_commits_event(self, mock_db):
        repo = PaymentEventRepository(mock_db)
        event = MagicMock(spec=PaymentEvent)
        event.id = uuid4()
        event.payment_id = uuid4()
        event.event_type = PaymentEventType.CREATED

        repo.create(event)

        mock_db.add.assert_called_once_with(event)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(event)

    def test_returns_the_event(self, mock_db):
        repo = PaymentEventRepository(mock_db)
        event = MagicMock(spec=PaymentEvent)
        event.id = uuid4()
        event.payment_id = uuid4()
        event.event_type = PaymentEventType.CALLBACK

        result = repo.create(event)
        assert result is event


class TestPaymentEventRepositoryGetById:
    """Tests for PaymentEventRepository.get_by_id."""

    def test_returns_event_when_found(self, mock_db):
        mock_event = MagicMock(spec=PaymentEvent)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_event
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.get_by_id(uuid4())
        assert result is mock_event

    def test_returns_none_when_not_found(self, mock_db):
        repo = PaymentEventRepository(mock_db)
        result = repo.get_by_id(uuid4())
        assert result is None


class TestPaymentEventRepositoryGetByPaymentId:
    """Tests for PaymentEventRepository.get_by_payment_id."""

    def test_returns_events_list(self, mock_db):
        events = [MagicMock(spec=PaymentEvent), MagicMock(spec=PaymentEvent)]
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = events
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.get_by_payment_id(uuid4())
        assert len(result) == 2

    def test_respects_limit_parameter(self, mock_db):
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        repo.get_by_payment_id(uuid4(), limit=10)
        query_mock.limit.assert_called_with(10)


class TestPaymentEventRepositoryGetByProviderEventId:
    """Tests for PaymentEventRepository.get_by_provider_event_id."""

    def test_returns_event_when_found(self, mock_db):
        mock_event = MagicMock(spec=PaymentEvent)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_event
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.get_by_provider_event_id("evt_123")
        assert result is mock_event


class TestPaymentEventRepositoryHasCallbackBeenProcessed:
    """Tests for PaymentEventRepository.has_callback_been_processed."""

    def test_returns_true_when_provider_event_exists(self, mock_db):
        existing_event = MagicMock(spec=PaymentEvent)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = existing_event
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.has_callback_been_processed(uuid4(), "evt_dup", "hash_123")
        assert result is True

    def test_returns_false_when_no_provider_event(self, mock_db):
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.has_callback_been_processed(uuid4(), None, "hash_123")
        assert result is False

    def test_returns_false_when_provider_event_id_is_none(self, mock_db):
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        repo = PaymentEventRepository(mock_db)
        result = repo.has_callback_been_processed(uuid4(), None, "hash_xyz")
        assert result is False
