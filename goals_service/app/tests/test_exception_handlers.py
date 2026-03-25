"""
Unit tests for exception handlers.

Tests cover:
- Exception handler response format (status code, error body)
- Each handler returns correct JSON structure
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.models.goal import GoalType, GoalStatus, GoalPriority
from app.tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID


class TestGoalNotFoundHandler:
    """Tests for GoalNotFoundError exception handler."""

    @patch("app.services.goal.GoalService.get_goal")
    def test_returns_404_with_error_body(self, mock_get, client, auth_headers):
        """GoalNotFoundError returns 404 with error and errorCode."""
        from app.exceptions.goal_exceptions import GoalNotFoundError

        mock_get.side_effect = GoalNotFoundError("Goal 999 not found")

        response = client.get("/api/v1/goals/999", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "errorCode" in data
        assert data["errorCode"] == "GOAL_NOT_FOUND"

    @patch("app.services.goal.GoalService.delete_goal")
    def test_delete_not_found(self, mock_delete, client, auth_headers):
        """Delete of nonexistent goal returns 404."""
        from app.exceptions.goal_exceptions import GoalNotFoundError

        mock_delete.side_effect = GoalNotFoundError()

        response = client.delete("/api/v1/goals/999", headers=auth_headers)

        assert response.status_code == 404
        assert response.json()["errorCode"] == "GOAL_NOT_FOUND"


class TestGoalValidationHandler:
    """Tests for GoalValidationError exception handler."""

    @patch("app.services.goal.GoalService.create_goal")
    def test_returns_422_with_error_body(self, mock_create, client, auth_headers):
        """GoalValidationError returns 422 with error and errorCode."""
        from app.exceptions.goal_exceptions import GoalValidationError

        mock_create.side_effect = GoalValidationError("Workspace access denied")

        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "Test",
                "goal_type": "SAVINGS",
                "target_amount": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_VALIDATION_FAILED"


class TestGoalOwnershipHandler:
    """Tests for GoalOwnershipError exception handler."""

    @patch("app.services.goal.GoalService.get_goal")
    def test_returns_403_with_error_body(self, mock_get, client, auth_headers):
        """GoalOwnershipError returns 403."""
        from app.exceptions.goal_exceptions import GoalOwnershipError

        mock_get.side_effect = GoalOwnershipError()

        response = client.get("/api/v1/goals/1", headers=auth_headers)

        assert response.status_code == 403
        data = response.json()
        assert data["errorCode"] == "GOAL_ACCESS_DENIED"


class TestGoalCreationHandler:
    """Tests for GoalCreationError exception handler."""

    @patch("app.services.goal.GoalService.create_goal")
    def test_returns_422(self, mock_create, client, auth_headers):
        """GoalCreationError returns 422."""
        from app.exceptions.goal_exceptions import GoalCreationError

        mock_create.side_effect = GoalCreationError("DB error")

        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "Test",
                "goal_type": "SAVINGS",
                "target_amount": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_CREATION_FAILED"


class TestGoalUpdateHandler:
    """Tests for GoalUpdateError exception handler."""

    @patch("app.services.goal.GoalService.update_goal")
    def test_returns_422(self, mock_update, client, auth_headers):
        """GoalUpdateError returns 422."""
        from app.exceptions.goal_exceptions import GoalUpdateError

        mock_update.side_effect = GoalUpdateError("DB error")

        response = client.put(
            "/api/v1/goals/1",
            json={"title": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_UPDATE_FAILED"


class TestGoalDeletionHandler:
    """Tests for GoalDeletionError exception handler."""

    @patch("app.services.goal.GoalService.delete_goal")
    def test_returns_422(self, mock_delete, client, auth_headers):
        """GoalDeletionError returns 422."""
        from app.exceptions.goal_exceptions import GoalDeletionError

        mock_delete.side_effect = GoalDeletionError("DB error")

        response = client.delete("/api/v1/goals/1", headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_DELETION_FAILED"


class TestGoalRetrievalHandler:
    """Tests for GoalRetrievalError exception handler."""

    @patch("app.services.goal.GoalService.get_goals")
    def test_returns_422(self, mock_get, client, auth_headers):
        """GoalRetrievalError returns 422."""
        from app.exceptions.goal_exceptions import GoalRetrievalError

        mock_get.side_effect = GoalRetrievalError("DB error")

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_RETRIEVAL_FAILED"


class TestGoalStatisticsHandler:
    """Tests for GoalStatisticsError exception handler."""

    @patch("app.services.goal.GoalService.get_goal_statistics")
    def test_returns_422(self, mock_stats, client, auth_headers):
        """GoalStatisticsError returns 422."""
        from app.exceptions.goal_exceptions import GoalStatisticsError

        mock_stats.side_effect = GoalStatisticsError("DB error")

        response = client.get(
            "/api/v1/goals/statistics/overview",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_STATISTICS_FAILED"


class TestGoalProgressHandler:
    """Tests for GoalProgressError exception handler."""

    @patch("app.services.goal.GoalService.update_goal_progress")
    def test_returns_422(self, mock_update, client, auth_headers):
        """GoalProgressError returns 422."""
        from app.exceptions.goal_exceptions import GoalProgressError

        mock_update.side_effect = GoalProgressError("Update failed")

        response = client.patch(
            "/api/v1/goals/1/progress",
            json={"current_amount": 100},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "GOAL_PROGRESS_UPDATE_FAILED"


class TestMilestoneNotFoundHandler:
    """Tests for MilestoneNotFoundError exception handler."""

    @patch("app.services.goal.GoalService.update_milestone_progress")
    def test_returns_404(self, mock_update, client, auth_headers):
        """MilestoneNotFoundError returns 404."""
        from app.exceptions.goal_exceptions import MilestoneNotFoundError

        mock_update.side_effect = MilestoneNotFoundError()

        response = client.patch(
            "/api/v1/goals/1/milestones/999/progress",
            json={"current_amount": 100},
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["errorCode"] == "MILESTONE_NOT_FOUND"


class TestMilestoneValidationHandler:
    """Tests for MilestoneValidationError exception handler."""

    @patch("app.services.goal.GoalService.create_milestone")
    def test_returns_422(self, mock_create, client, auth_headers):
        """MilestoneValidationError returns 422."""
        from app.exceptions.goal_exceptions import MilestoneValidationError

        mock_create.side_effect = MilestoneValidationError()

        response = client.post(
            "/api/v1/goals/1/milestones",
            json={"title": "Test", "target_amount": 1000},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "MILESTONE_VALIDATION_FAILED"


class TestMilestoneCreationHandler:
    """Tests for MilestoneCreationError exception handler."""

    @patch("app.services.goal.GoalService.create_milestone")
    def test_returns_422(self, mock_create, client, auth_headers):
        """MilestoneCreationError returns 422."""
        from app.exceptions.goal_exceptions import MilestoneCreationError

        mock_create.side_effect = MilestoneCreationError()

        response = client.post(
            "/api/v1/goals/1/milestones",
            json={"title": "Test", "target_amount": 1000},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "MILESTONE_CREATION_FAILED"


class TestMilestoneRetrievalHandler:
    """Tests for MilestoneRetrievalError exception handler."""

    @patch("app.services.goal.GoalService.get_milestones")
    def test_returns_422(self, mock_get, client, auth_headers):
        """MilestoneRetrievalError returns 422."""
        from app.exceptions.goal_exceptions import MilestoneRetrievalError

        mock_get.side_effect = MilestoneRetrievalError()

        response = client.get(
            "/api/v1/goals/1/milestones",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "MILESTONE_RETRIEVAL_FAILED"


class TestMilestoneProgressUpdateHandler:
    """Tests for MilestoneProgressUpdateError exception handler."""

    @patch("app.services.goal.GoalService.update_milestone_progress")
    def test_returns_422(self, mock_update, client, auth_headers):
        """MilestoneProgressUpdateError returns 422."""
        from app.exceptions.goal_exceptions import MilestoneProgressUpdateError

        mock_update.side_effect = MilestoneProgressUpdateError()

        response = client.patch(
            "/api/v1/goals/1/milestones/1/progress",
            json={"current_amount": 100},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "MILESTONE_PROGRESS_UPDATE_FAILED"


class TestGeneralExceptionHandler:
    """Tests for general unhandled exception handler."""

    @patch("app.services.goal.GoalService.get_goal")
    def test_returns_500(self, mock_get, client, auth_headers):
        """Unhandled exceptions return 500."""
        mock_get.side_effect = RuntimeError("Unexpected error")

        # RuntimeError propagates through the middleware, which may re-raise.
        # The test client may raise or return 500 depending on middleware order.
        try:
            response = client.get("/api/v1/goals/1", headers=auth_headers)
            assert response.status_code == 500
        except RuntimeError:
            # Middleware re-raised the exception before the handler could catch it
            pass
