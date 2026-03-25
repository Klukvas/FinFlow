"""Tests for the subscription status state machine."""

from __future__ import annotations

import pytest

from app.services.state_machine import (
    validate_transition,
    InvalidTransitionError,
    VALID_STATUSES,
    ALLOWED_TRANSITIONS,
    EVENT_TO_STATUS,
)


class TestValidateTransition:
    """Tests for validate_transition function."""

    # ----- Happy-path transitions -----

    def test_active_to_past_due(self):
        result = validate_transition("active", "past_due")
        assert result == "past_due"

    def test_active_to_canceled(self):
        result = validate_transition("active", "canceled")
        assert result == "canceled"

    def test_active_to_paused(self):
        result = validate_transition("active", "paused")
        assert result == "paused"

    def test_past_due_to_active_via_activated(self):
        result = validate_transition("past_due", "activated")
        assert result == "active"

    def test_past_due_to_active_via_resumed(self):
        result = validate_transition("past_due", "resumed")
        assert result == "active"

    def test_past_due_to_canceled(self):
        result = validate_transition("past_due", "canceled")
        assert result == "canceled"

    def test_paused_to_active_via_activated(self):
        result = validate_transition("paused", "activated")
        assert result == "active"

    def test_paused_to_active_via_resumed(self):
        result = validate_transition("paused", "resumed")
        assert result == "active"

    def test_paused_to_canceled(self):
        result = validate_transition("paused", "canceled")
        assert result == "canceled"

    def test_canceled_to_active_via_activated(self):
        """Reactivation: canceled -> active."""
        result = validate_transition("canceled", "activated")
        assert result == "active"

    def test_canceled_to_active_via_resumed(self):
        """Reactivation: canceled -> active via resumed."""
        result = validate_transition("canceled", "resumed")
        assert result == "active"

    # ----- Same-status (no-op) transitions -----

    def test_active_to_active_is_noop(self):
        result = validate_transition("active", "activated")
        assert result == "active"

    def test_canceled_to_canceled_is_noop(self):
        result = validate_transition("canceled", "canceled")
        assert result == "canceled"

    def test_past_due_to_past_due_is_noop(self):
        result = validate_transition("past_due", "past_due")
        assert result == "past_due"

    def test_paused_to_paused_is_noop(self):
        result = validate_transition("paused", "paused")
        assert result == "paused"

    # ----- Invalid transitions -----

    def test_canceled_to_past_due_raises(self):
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_transition("canceled", "past_due")
        assert exc_info.value.current == "canceled"
        assert exc_info.value.target == "past_due"

    def test_canceled_to_paused_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition("canceled", "paused")

    def test_paused_to_past_due_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition("paused", "past_due")

    def test_active_to_active_via_resumed_is_noop(self):
        """active -> resumed -> active is just a no-op (same target status)."""
        result = validate_transition("active", "resumed")
        assert result == "active"

    # ----- Unknown event type -----

    def test_unknown_event_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown Paddle event type"):
            validate_transition("active", "nonexistent_event")

    def test_empty_event_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown Paddle event type"):
            validate_transition("active", "")


class TestInvalidTransitionError:
    """Tests for InvalidTransitionError exception."""

    def test_attributes_set_correctly(self):
        error = InvalidTransitionError("active", "paused_x", "some_event")
        assert error.current == "active"
        assert error.target == "paused_x"
        assert error.event_type == "some_event"

    def test_message_format(self):
        error = InvalidTransitionError("active", "past_due", "test_event")
        assert "active" in str(error)
        assert "past_due" in str(error)
        assert "test_event" in str(error)


class TestConstants:
    """Tests for state machine constants."""

    def test_valid_statuses_are_frozenset(self):
        assert isinstance(VALID_STATUSES, frozenset)

    def test_valid_statuses_contains_expected(self):
        assert VALID_STATUSES == {"active", "past_due", "canceled", "paused"}

    def test_all_statuses_have_transitions(self):
        for status in VALID_STATUSES:
            assert status in ALLOWED_TRANSITIONS

    def test_event_to_status_mapping(self):
        assert EVENT_TO_STATUS["activated"] == "active"
        assert EVENT_TO_STATUS["resumed"] == "active"
        assert EVENT_TO_STATUS["canceled"] == "canceled"
        assert EVENT_TO_STATUS["past_due"] == "past_due"
        assert EVENT_TO_STATUS["paused"] == "paused"

    def test_all_target_statuses_are_valid(self):
        for targets in ALLOWED_TRANSITIONS.values():
            for target in targets:
                assert target in VALID_STATUSES, f"{target} not in VALID_STATUSES"
