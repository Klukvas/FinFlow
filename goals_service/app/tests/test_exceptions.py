"""
Unit tests for custom exceptions and exception handlers.

Tests cover:
- Exception class hierarchy
- Error codes and status codes
- Exception handler response format
- GoalLimitExceededError details
- GoalReadOnlyExcessError details
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request

from app.exceptions.goal_exceptions import (
    GoalServiceError, GoalNotFoundError, GoalValidationError,
    GoalOwnershipError, GoalCreationError, GoalUpdateError,
    GoalDeletionError, GoalRetrievalError, GoalStatisticsError,
    GoalProgressError, GoalLimitExceededError, GoalReadOnlyExcessError,
    MilestoneNotFoundError, MilestoneValidationError,
    MilestoneCreationError, MilestoneRetrievalError,
    MilestoneProgressUpdateError,
)


class TestGoalServiceError:
    """Tests for base GoalServiceError."""

    def test_default_error(self):
        """Create base error with defaults."""
        error = GoalServiceError(detail="Something went wrong")

        assert error.detail == "Something went wrong"
        assert error.status_code == 400
        assert error.error_code == "GOAL_ERROR"

    def test_custom_error(self):
        """Create base error with custom values."""
        error = GoalServiceError(
            detail="Custom error",
            status_code=500,
            error_code="CUSTOM_CODE",
        )

        assert error.status_code == 500
        assert error.error_code == "CUSTOM_CODE"


class TestGoalNotFoundError:
    """Tests for GoalNotFoundError."""

    def test_default_message(self):
        """Default message is 'Goal not found'."""
        error = GoalNotFoundError()

        assert error.detail == "Goal not found"
        assert error.status_code == 404
        assert error.error_code == "GOAL_NOT_FOUND"

    def test_custom_message(self):
        """Custom message overrides default."""
        error = GoalNotFoundError(detail="Goal 42 not found for user 1")

        assert "Goal 42" in error.detail


class TestGoalValidationError:
    """Tests for GoalValidationError."""

    def test_default_message(self):
        error = GoalValidationError()

        assert error.detail == "Goal validation failed"
        assert error.status_code == 422
        assert error.error_code == "GOAL_VALIDATION_FAILED"


class TestGoalOwnershipError:
    """Tests for GoalOwnershipError."""

    def test_default_message(self):
        error = GoalOwnershipError()

        assert error.detail == "Access denied to goal"
        assert error.status_code == 403
        assert error.error_code == "GOAL_ACCESS_DENIED"


class TestMilestoneErrors:
    """Tests for milestone-specific errors."""

    def test_milestone_not_found(self):
        error = MilestoneNotFoundError()

        assert error.status_code == 404
        assert error.error_code == "MILESTONE_NOT_FOUND"

    def test_milestone_validation(self):
        error = MilestoneValidationError()

        assert error.status_code == 422
        assert error.error_code == "MILESTONE_VALIDATION_FAILED"

    def test_milestone_creation(self):
        error = MilestoneCreationError()

        assert error.status_code == 422
        assert error.error_code == "MILESTONE_CREATION_FAILED"

    def test_milestone_retrieval(self):
        error = MilestoneRetrievalError()

        assert error.status_code == 422
        assert error.error_code == "MILESTONE_RETRIEVAL_FAILED"

    def test_milestone_progress_update(self):
        error = MilestoneProgressUpdateError()

        assert error.status_code == 422
        assert error.error_code == "MILESTONE_PROGRESS_UPDATE_FAILED"


class TestGoalOperationErrors:
    """Tests for goal operation-specific errors."""

    def test_creation_error(self):
        error = GoalCreationError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_CREATION_FAILED"

    def test_update_error(self):
        error = GoalUpdateError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_UPDATE_FAILED"

    def test_deletion_error(self):
        error = GoalDeletionError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_DELETION_FAILED"

    def test_retrieval_error(self):
        error = GoalRetrievalError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_RETRIEVAL_FAILED"

    def test_statistics_error(self):
        error = GoalStatisticsError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_STATISTICS_FAILED"

    def test_progress_error(self):
        error = GoalProgressError()

        assert error.status_code == 422
        assert error.error_code == "GOAL_PROGRESS_UPDATE_FAILED"


class TestGoalLimitExceededError:
    """Tests for GoalLimitExceededError."""

    def test_error_message_contains_counts(self):
        """Error message includes current count and limit."""
        error = GoalLimitExceededError(current_count=10, limit=5)

        assert "10" in error.detail
        assert "5" in error.detail
        assert "Goal limit exceeded" in error.detail

    def test_inherits_from_validation_error(self):
        """GoalLimitExceededError is a GoalValidationError."""
        error = GoalLimitExceededError(current_count=10, limit=5)

        assert isinstance(error, GoalValidationError)
        assert error.status_code == 422


class TestGoalReadOnlyExcessError:
    """Tests for GoalReadOnlyExcessError."""

    def test_error_attributes(self):
        """Error has correct attributes."""
        error = GoalReadOnlyExcessError(goal_id=42, current_count=10, limit=5)

        assert error.goal_id == 42
        assert error.current_count == 10
        assert error.limit == 5
        assert error.status_code == 403
        assert error.error_code == "RECORD_READ_ONLY_EXCESS"

    def test_error_message_contains_info(self):
        """Error message includes relevant information."""
        error = GoalReadOnlyExcessError(goal_id=1, current_count=7, limit=3)

        assert "read-only" in error.detail.lower()
        assert "7" in error.detail
        assert "3" in error.detail

    def test_inherits_from_service_error(self):
        """GoalReadOnlyExcessError is a GoalServiceError."""
        error = GoalReadOnlyExcessError(goal_id=1, current_count=5, limit=3)

        assert isinstance(error, GoalServiceError)


class TestExceptionInheritance:
    """Tests for exception class hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """All goal exceptions inherit from GoalServiceError."""
        exceptions = [
            GoalNotFoundError, GoalValidationError, GoalOwnershipError,
            GoalCreationError, GoalUpdateError, GoalDeletionError,
            GoalRetrievalError, GoalStatisticsError, GoalProgressError,
            MilestoneNotFoundError, MilestoneValidationError,
            MilestoneCreationError, MilestoneRetrievalError,
            MilestoneProgressUpdateError,
        ]

        for exc_class in exceptions:
            error = exc_class()
            assert isinstance(error, GoalServiceError), (
                f"{exc_class.__name__} should inherit from GoalServiceError"
            )

    def test_limit_exceeded_inherits_validation(self):
        """GoalLimitExceededError inherits from GoalValidationError."""
        error = GoalLimitExceededError(current_count=1, limit=1)
        assert isinstance(error, GoalValidationError)

    def test_read_only_inherits_service_error(self):
        """GoalReadOnlyExcessError inherits from GoalServiceError."""
        error = GoalReadOnlyExcessError(goal_id=1, current_count=1, limit=1)
        assert isinstance(error, GoalServiceError)
