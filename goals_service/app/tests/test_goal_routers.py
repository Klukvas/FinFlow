"""
Unit tests for Goal API Routers.

Tests cover:
- POST /api/v1/goals/ - Create goal
- GET /api/v1/goals/ - List goals
- GET /api/v1/goals/{id} - Get single goal
- PUT /api/v1/goals/{id} - Update goal
- PATCH /api/v1/goals/{id}/progress - Update progress
- DELETE /api/v1/goals/{id} - Delete goal
- GET /api/v1/goals/statistics/overview - Get statistics
- POST /api/v1/goals/{id}/milestones - Create milestone
- GET /api/v1/goals/{id}/milestones - List milestones
- PATCH /api/v1/goals/{id}/milestones/{mid}/progress - Update milestone progress
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models.goal import Goal, GoalType, GoalStatus, GoalPriority
from app.models.milestone import Milestone
from app.tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID


# ==================== Create Goal Endpoint ====================

class TestCreateGoalEndpoint:
    """Tests for POST /api/v1/goals/"""

    @patch("app.services.goal.GoalService.create_goal")
    def test_create_goal_success(self, mock_create, client, auth_headers):
        """Successfully create a goal via API."""
        mock_goal = MagicMock()
        mock_goal.id = 1
        mock_goal.user_id = TEST_USER_ID
        mock_goal.workspace_id = TEST_WORKSPACE_ID
        mock_goal.title = "Save for vacation"
        mock_goal.description = "Trip to Japan"
        mock_goal.goal_type = GoalType.SAVINGS
        mock_goal.priority = GoalPriority.HIGH
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.target_amount = 5000.00
        mock_goal.current_amount = 0.0
        mock_goal.currency = "USD"
        mock_goal.progress_percentage = 0.0
        mock_goal.is_milestone_based = False
        mock_goal.target_date = None
        mock_goal.start_date = datetime.now(timezone.utc)
        mock_goal.created_at = datetime.now(timezone.utc)
        mock_goal.updated_at = None
        mock_create.return_value = mock_goal

        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "Save for vacation",
                "description": "Trip to Japan",
                "goal_type": "SAVINGS",
                "priority": "HIGH",
                "target_amount": 5000.00,
                "currency": "USD",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Save for vacation"
        assert data["goal_type"] == "SAVINGS"

    def test_create_goal_missing_required_fields(self, client, auth_headers):
        """Reject request with missing required fields."""
        response = client.post(
            "/api/v1/goals/",
            json={"description": "No title or type"},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_goal_invalid_target_amount(self, client, auth_headers):
        """Reject goal with zero or negative target amount."""
        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "Bad amount",
                "goal_type": "SAVINGS",
                "target_amount": -100,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_goal_invalid_goal_type(self, client, auth_headers):
        """Reject goal with invalid goal type."""
        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "Bad type",
                "goal_type": "INVALID_TYPE",
                "target_amount": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_goal_empty_title(self, client, auth_headers):
        """Reject goal with empty title."""
        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "",
                "goal_type": "SAVINGS",
                "target_amount": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_goal_title_too_long(self, client, auth_headers):
        """Reject goal with title exceeding max length."""
        response = client.post(
            "/api/v1/goals/",
            json={
                "title": "x" * 256,
                "goal_type": "SAVINGS",
                "target_amount": 1000,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422


# ==================== Get Goals Endpoint ====================

class TestGetGoalsEndpoint:
    """Tests for GET /api/v1/goals/"""

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_get_goals_success(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """Successfully list goals."""
        mock_goal = MagicMock()
        mock_goal.id = 1
        mock_goal.user_id = TEST_USER_ID
        mock_goal.workspace_id = TEST_WORKSPACE_ID
        mock_goal.title = "Test goal"
        mock_goal.description = None
        mock_goal.goal_type = GoalType.SAVINGS
        mock_goal.priority = GoalPriority.MEDIUM
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.target_amount = 1000.00
        mock_goal.current_amount = 500.00
        mock_goal.currency = "USD"
        mock_goal.progress_percentage = 50.0
        mock_goal.is_milestone_based = False
        mock_goal.target_date = None
        mock_goal.start_date = datetime.now(timezone.utc)
        mock_goal.created_at = datetime.now(timezone.utc)
        mock_goal.updated_at = None

        mock_get.return_value = [mock_goal]
        mock_ordered.return_value = [1]

        mock_sub_client = MagicMock()
        mock_sub_client.get_read_only_ids.return_value = set()
        mock_sub_instance.return_value = mock_sub_client

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_get_goals_empty(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """Return empty list when no goals exist."""
        mock_get.return_value = []
        mock_ordered.return_value = []

        mock_sub_client = MagicMock()
        mock_sub_client.get_read_only_ids.return_value = set()
        mock_sub_instance.return_value = mock_sub_client

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_get_goals_with_status_filter(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """Accepts status query parameter."""
        mock_get.return_value = []
        mock_ordered.return_value = []
        mock_sub_client = MagicMock()
        mock_sub_client.get_read_only_ids.return_value = set()
        mock_sub_instance.return_value = mock_sub_client

        response = client.get(
            "/api/v1/goals/?status=ACTIVE",
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_get_goals_invalid_skip(self, client, auth_headers):
        """Reject negative skip value."""
        response = client.get(
            "/api/v1/goals/?skip=-1",
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_get_goals_invalid_limit(self, client, auth_headers):
        """Reject limit exceeding maximum."""
        response = client.get(
            "/api/v1/goals/?limit=1001",
            headers=auth_headers,
        )

        assert response.status_code == 422


# ==================== Get Single Goal Endpoint ====================

class TestGetGoalEndpoint:
    """Tests for GET /api/v1/goals/{goal_id}"""

    @patch("app.services.goal.GoalService.get_goal")
    def test_get_goal_success(self, mock_get, client, auth_headers):
        """Successfully retrieve a single goal."""
        mock_goal = MagicMock()
        mock_goal.id = 1
        mock_goal.user_id = TEST_USER_ID
        mock_goal.workspace_id = TEST_WORKSPACE_ID
        mock_goal.title = "Test goal"
        mock_goal.description = None
        mock_goal.goal_type = GoalType.SAVINGS
        mock_goal.priority = GoalPriority.MEDIUM
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.target_amount = 1000.00
        mock_goal.current_amount = 500.00
        mock_goal.currency = "USD"
        mock_goal.progress_percentage = 50.0
        mock_goal.is_milestone_based = False
        mock_goal.target_date = None
        mock_goal.start_date = datetime.now(timezone.utc)
        mock_goal.created_at = datetime.now(timezone.utc)
        mock_goal.updated_at = None
        mock_get.return_value = mock_goal

        response = client.get("/api/v1/goals/1", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test goal"

    @patch("app.services.goal.GoalService.get_goal")
    def test_get_goal_not_found(self, mock_get, client, auth_headers):
        """Return 404 when goal not found."""
        from app.exceptions.goal_exceptions import GoalNotFoundError

        mock_get.side_effect = GoalNotFoundError("Goal 999 not found")

        response = client.get("/api/v1/goals/999", headers=auth_headers)

        assert response.status_code == 404


# ==================== Update Goal Endpoint ====================

class TestUpdateGoalEndpoint:
    """Tests for PUT /api/v1/goals/{goal_id}"""

    @patch("app.services.goal.GoalService.update_goal")
    def test_update_goal_success(self, mock_update, client, auth_headers):
        """Successfully update a goal."""
        mock_goal = MagicMock()
        mock_goal.id = 1
        mock_goal.user_id = TEST_USER_ID
        mock_goal.workspace_id = TEST_WORKSPACE_ID
        mock_goal.title = "Updated title"
        mock_goal.description = None
        mock_goal.goal_type = GoalType.SAVINGS
        mock_goal.priority = GoalPriority.HIGH
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.target_amount = 2000.00
        mock_goal.current_amount = 500.00
        mock_goal.currency = "USD"
        mock_goal.progress_percentage = 25.0
        mock_goal.is_milestone_based = False
        mock_goal.target_date = None
        mock_goal.start_date = datetime.now(timezone.utc)
        mock_goal.created_at = datetime.now(timezone.utc)
        mock_goal.updated_at = datetime.now(timezone.utc)
        mock_update.return_value = mock_goal

        response = client.put(
            "/api/v1/goals/1",
            json={"title": "Updated title", "target_amount": 2000.00},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"

    def test_update_goal_invalid_target_amount(self, client, auth_headers):
        """Reject update with negative target amount."""
        response = client.put(
            "/api/v1/goals/1",
            json={"target_amount": -500},
            headers=auth_headers,
        )

        assert response.status_code == 422

    @patch("app.services.goal.GoalService.update_goal")
    def test_update_goal_not_found(self, mock_update, client, auth_headers):
        """Return 404 when goal not found."""
        from app.exceptions.goal_exceptions import GoalNotFoundError

        mock_update.side_effect = GoalNotFoundError("Goal 999 not found")

        response = client.put(
            "/api/v1/goals/999",
            json={"title": "Ghost goal"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @patch("app.services.goal.GoalService.update_goal")
    def test_update_goal_read_only(self, mock_update, client, auth_headers):
        """Return 403 when goal is read-only due to plan limits."""
        from app.exceptions.goal_exceptions import GoalReadOnlyExcessError

        mock_update.side_effect = GoalReadOnlyExcessError(
            goal_id=1, current_count=5, limit=3
        )

        response = client.put(
            "/api/v1/goals/1",
            json={"title": "Should fail"},
            headers=auth_headers,
        )

        assert response.status_code == 403


# ==================== Update Goal Progress Endpoint ====================

class TestUpdateGoalProgressEndpoint:
    """Tests for PATCH /api/v1/goals/{goal_id}/progress"""

    @patch("app.services.goal.GoalService.update_goal_progress")
    def test_update_progress_success(self, mock_update, client, auth_headers):
        """Successfully update goal progress."""
        mock_goal = MagicMock()
        mock_goal.id = 1
        mock_goal.user_id = TEST_USER_ID
        mock_goal.workspace_id = TEST_WORKSPACE_ID
        mock_goal.title = "Goal"
        mock_goal.description = None
        mock_goal.goal_type = GoalType.SAVINGS
        mock_goal.priority = GoalPriority.MEDIUM
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.target_amount = 1000.00
        mock_goal.current_amount = 750.00
        mock_goal.currency = "USD"
        mock_goal.progress_percentage = 75.0
        mock_goal.is_milestone_based = False
        mock_goal.target_date = None
        mock_goal.start_date = datetime.now(timezone.utc)
        mock_goal.created_at = datetime.now(timezone.utc)
        mock_goal.updated_at = datetime.now(timezone.utc)
        mock_update.return_value = mock_goal

        response = client.patch(
            "/api/v1/goals/1/progress",
            json={"current_amount": 750.00},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_amount"] == 750.0

    def test_update_progress_negative_amount(self, client, auth_headers):
        """Reject negative current amount."""
        response = client.patch(
            "/api/v1/goals/1/progress",
            json={"current_amount": -100},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_update_progress_missing_amount(self, client, auth_headers):
        """Reject request without current_amount field."""
        response = client.patch(
            "/api/v1/goals/1/progress",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 422


# ==================== Delete Goal Endpoint ====================

class TestDeleteGoalEndpoint:
    """Tests for DELETE /api/v1/goals/{goal_id}"""

    @patch("app.services.goal.GoalService.delete_goal")
    def test_delete_goal_success(self, mock_delete, client, auth_headers):
        """Successfully delete a goal."""
        mock_delete.return_value = True

        response = client.delete("/api/v1/goals/1", headers=auth_headers)

        assert response.status_code == 204

    @patch("app.services.goal.GoalService.delete_goal")
    def test_delete_goal_not_found(self, mock_delete, client, auth_headers):
        """Return 404 when goal not found."""
        from app.exceptions.goal_exceptions import GoalNotFoundError

        mock_delete.side_effect = GoalNotFoundError("Goal 999 not found")

        response = client.delete("/api/v1/goals/999", headers=auth_headers)

        assert response.status_code == 404


# ==================== Statistics Endpoint ====================

class TestStatisticsEndpoint:
    """Tests for GET /api/v1/goals/statistics/overview"""

    @patch("app.services.goal.GoalService.get_goal_statistics")
    def test_get_statistics_success(self, mock_stats, client, auth_headers):
        """Successfully retrieve goal statistics."""
        mock_stats.return_value = {
            "total_goals": 5,
            "active_goals": 3,
            "completed_goals": 2,
            "total_target_amount": 50000.0,
            "total_current_amount": 25000.0,
            "overall_progress": 50.0,
            "currency": "USD",
            "goals_by_type": {"SAVINGS": 3, "INVESTMENT": 2},
            "goals_by_priority": {"HIGH": 2, "MEDIUM": 3},
        }

        response = client.get(
            "/api/v1/goals/statistics/overview",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_goals"] == 5
        assert data["active_goals"] == 3
        assert data["overall_progress"] == 50.0

    @patch("app.services.goal.GoalService.get_goal_statistics")
    def test_get_statistics_empty(self, mock_stats, client, auth_headers):
        """Return zero statistics when no goals exist."""
        mock_stats.return_value = {
            "total_goals": 0,
            "active_goals": 0,
            "completed_goals": 0,
            "total_target_amount": 0.0,
            "total_current_amount": 0.0,
            "overall_progress": 0.0,
            "currency": "USD",
            "goals_by_type": {},
            "goals_by_priority": {},
        }

        response = client.get(
            "/api/v1/goals/statistics/overview",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_goals"] == 0


# ==================== Milestone Endpoints ====================

class TestMilestoneEndpoints:
    """Tests for milestone-related endpoints."""

    @patch("app.services.goal.GoalService.create_milestone")
    def test_create_milestone_success(self, mock_create, client, auth_headers):
        """Successfully create a milestone."""
        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.goal_id = 1
        mock_milestone.title = "First milestone"
        mock_milestone.description = None
        mock_milestone.target_amount = 1000.00
        mock_milestone.current_amount = 0.0
        mock_milestone.is_completed = False
        mock_milestone.completed_at = None
        mock_milestone.order_index = 0
        mock_milestone.created_at = datetime.now(timezone.utc)
        mock_milestone.updated_at = None
        mock_create.return_value = mock_milestone

        response = client.post(
            "/api/v1/goals/1/milestones",
            json={
                "title": "First milestone",
                "target_amount": 1000.00,
                "order_index": 0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "First milestone"

    def test_create_milestone_missing_title(self, client, auth_headers):
        """Reject milestone without title."""
        response = client.post(
            "/api/v1/goals/1/milestones",
            json={"target_amount": 1000.00},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_milestone_invalid_amount(self, client, auth_headers):
        """Reject milestone with negative target amount."""
        response = client.post(
            "/api/v1/goals/1/milestones",
            json={"title": "Bad milestone", "target_amount": -500},
            headers=auth_headers,
        )

        assert response.status_code == 422

    @patch("app.services.goal.GoalService.get_milestones")
    def test_get_milestones_success(self, mock_get, client, auth_headers):
        """Successfully list milestones for a goal."""
        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.goal_id = 1
        mock_milestone.title = "Milestone 1"
        mock_milestone.description = None
        mock_milestone.target_amount = 1000.00
        mock_milestone.current_amount = 500.00
        mock_milestone.is_completed = False
        mock_milestone.completed_at = None
        mock_milestone.order_index = 0
        mock_milestone.created_at = datetime.now(timezone.utc)
        mock_milestone.updated_at = None
        mock_get.return_value = [mock_milestone]

        response = client.get("/api/v1/goals/1/milestones", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Milestone 1"

    @patch("app.services.goal.GoalService.update_milestone_progress")
    def test_update_milestone_progress_success(
        self, mock_update, client, auth_headers
    ):
        """Successfully update milestone progress."""
        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.goal_id = 1
        mock_milestone.title = "Milestone 1"
        mock_milestone.description = None
        mock_milestone.target_amount = 1000.00
        mock_milestone.current_amount = 800.00
        mock_milestone.is_completed = False
        mock_milestone.completed_at = None
        mock_milestone.order_index = 0
        mock_milestone.created_at = datetime.now(timezone.utc)
        mock_milestone.updated_at = datetime.now(timezone.utc)
        mock_update.return_value = mock_milestone

        response = client.patch(
            "/api/v1/goals/1/milestones/1/progress",
            json={"current_amount": 800.00},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_amount"] == 800.0

    @patch("app.services.goal.GoalService.update_milestone_progress")
    def test_update_milestone_not_found(self, mock_update, client, auth_headers):
        """Return 404 when milestone not found."""
        from app.exceptions.goal_exceptions import MilestoneNotFoundError

        mock_update.side_effect = MilestoneNotFoundError("Milestone 999 not found")

        response = client.patch(
            "/api/v1/goals/1/milestones/999/progress",
            json={"current_amount": 100.00},
            headers=auth_headers,
        )

        assert response.status_code == 404
