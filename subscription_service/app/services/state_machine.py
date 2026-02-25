"""Subscription status state machine with validated transitions."""
from __future__ import annotations

import logging

logger = logging.getLogger("subscription_service.state_machine")

# Valid statuses (must match DB CHECK constraint)
VALID_STATUSES = frozenset({"active", "past_due", "canceled", "paused"})

# Map: current_status -> set of allowed target statuses
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "active": frozenset({"past_due", "canceled", "paused"}),
    "past_due": frozenset({"active", "canceled"}),
    "paused": frozenset({"active", "canceled"}),
    "canceled": frozenset({"active"}),  # reactivation only
}

# Map Paddle event_type -> target subscription status
EVENT_TO_STATUS: dict[str, str] = {
    "activated": "active",
    "resumed": "active",
    "canceled": "canceled",
    "past_due": "past_due",
    "paused": "paused",
}


class InvalidTransitionError(Exception):
    """Raised when a status transition is not allowed."""

    def __init__(self, current: str, target: str, event_type: str) -> None:
        self.current = current
        self.target = target
        self.event_type = event_type
        super().__init__(
            f"Invalid subscription transition: {current} -> {target} "
            f"(triggered by event '{event_type}')"
        )


def validate_transition(current_status: str, event_type: str) -> str:
    """Validate and return the target status for a Paddle event.

    Args:
        current_status: Current subscription status.
        event_type: Paddle event type string.

    Returns:
        The validated target status.

    Raises:
        InvalidTransitionError: If the transition is not allowed.
        ValueError: If event_type is unknown.
    """
    target_status = EVENT_TO_STATUS.get(event_type)
    if target_status is None:
        raise ValueError(f"Unknown Paddle event type: {event_type}")

    # Same status is a no-op — always allowed
    if current_status == target_status:
        return target_status

    allowed = ALLOWED_TRANSITIONS.get(current_status, frozenset())
    if target_status not in allowed:
        raise InvalidTransitionError(current_status, target_status, event_type)

    return target_status
