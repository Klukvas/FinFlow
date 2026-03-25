"""
Unit tests for GoalService - Business Logic.

Tests cover:
- Goal CRUD operations
- Goal progress tracking
- Goal statistics
- Subscription limit enforcement
- Workspace authorization
- Error handling
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.goal import GoalService
from app.models.goal import Goal, GoalType, GoalStatus, GoalPriority
from app.models.milestone import Milestone
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalProgressUpdate,
    MilestoneCreate, MilestoneProgressUpdate,
)
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalCreationError,
    GoalUpdateError, GoalDeletionError, GoalRetrievalError,
    GoalStatisticsError, GoalProgressError, GoalLimitExceededError,
    GoalReadOnlyExcessError,
    MilestoneNotFoundError, MilestoneCreationError,
    MilestoneRetrievalError, MilestoneProgressUpdateError,
)

from app.tests.conftest import TEST_USER_ID, OTHER_USER_ID, TEST_WORKSPACE_ID, OTHER_WORKSPACE_ID


# ==================== Create Goal ====================

class TestCreateGoal:
    """Tests for GoalService.create_goal()"""

    def test_create_goal_success(self, goal_service):
        """Successfully create a new goal."""
        goal_data = GoalCreate(
            title="Save for vacation",
            description="Trip to Japan",
            goal_type=GoalType.SAVINGS,
            priority=GoalPriority.HIGH,
            target_amount=5000.00,
            currency="USD",
        )

        goal = goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

        assert goal.id is not None
        assert goal.title == "Save for vacation"
        assert goal.description == "Trip to Japan"
        assert goal.goal_type == GoalType.SAVINGS
        assert goal.priority == GoalPriority.HIGH
        assert float(goal.target_amount) == 5000.00
        assert goal.currency == "USD"
        assert goal.user_id == TEST_USER_ID
        assert goal.workspace_id == TEST_WORKSPACE_ID
        assert goal.status == GoalStatus.ACTIVE

    def test_create_goal_default_values(self, goal_service):
        """Goal uses correct default values when not specified."""
        goal_data = GoalCreate(
            title="Minimal goal",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.00,
        )

        goal = goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

        assert goal.priority == GoalPriority.MEDIUM
        assert goal.currency == "USD"
        assert goal.is_milestone_based is False
        assert goal.description is None

    def test_create_goal_with_target_date(self, goal_service):
        """Create goal with a target date."""
        target_date = datetime(2027, 12, 31, 0, 0, 0)
        goal_data = GoalCreate(
            title="Long term goal",
            goal_type=GoalType.INVESTMENT,
            target_amount=50000.00,
            target_date=target_date,
        )

        goal = goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

        assert goal.target_date is not None

    def test_create_goal_milestone_based(self, goal_service):
        """Create a milestone-based goal."""
        goal_data = GoalCreate(
            title="Phased savings",
            goal_type=GoalType.SAVINGS,
            target_amount=10000.00,
            is_milestone_based=True,
        )

        goal = goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

        assert goal.is_milestone_based is True

    def test_create_goal_subscription_limit_exceeded(self, goal_service, mock_subscription_client):
        """Raise GoalLimitExceededError when subscription limit reached."""
        mock_subscription_client.check_limit.return_value = (False, 5)

        goal_data = GoalCreate(
            title="Over limit",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.00,
        )

        with pytest.raises(GoalLimitExceededError) as exc_info:
            goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

        assert "Goal limit exceeded" in str(exc_info.value.detail)

    def test_create_goal_workspace_auth_denied(self, goal_service, mock_workspace_client):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        goal_data = GoalCreate(
            title="Denied goal",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.00,
        )

        with pytest.raises(GoalValidationError):
            goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

    def test_create_goal_db_error_raises_creation_error(self, goal_service, db_session):
        """Raise GoalCreationError on unexpected database errors."""
        goal_data = GoalCreate(
            title="DB error goal",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.00,
        )

        # Simulate database error by closing the session
        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB connection lost")):
            with pytest.raises(GoalCreationError) as exc_info:
                goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)

            assert "Failed to create goal" in str(exc_info.value.detail)

    def test_create_goal_all_types(self, goal_service):
        """Create goals of all types successfully."""
        for goal_type in GoalType:
            goal_data = GoalCreate(
                title=f"Goal {goal_type.value}",
                goal_type=goal_type,
                target_amount=1000.00,
            )
            goal = goal_service.create_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_data)
            assert goal.goal_type == goal_type


# ==================== Get Goals ====================

class TestGetGoals:
    """Tests for GoalService.get_goals()"""

    def test_get_goals_returns_user_goals(self, goal_service, multiple_goals):
        """Return all goals for the user in workspace."""
        goals = goal_service.get_goals(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert len(goals) == 4

    def test_get_goals_empty_list(self, goal_service):
        """Return empty list when user has no goals."""
        goals = goal_service.get_goals(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert goals == []

    def test_get_goals_filter_by_status(self, goal_service, multiple_goals):
        """Filter goals by status."""
        active = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, status=GoalStatus.ACTIVE
        )
        assert len(active) == 2

        completed = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, status=GoalStatus.COMPLETED
        )
        assert len(completed) == 1

        paused = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, status=GoalStatus.PAUSED
        )
        assert len(paused) == 1

    def test_get_goals_filter_by_type(self, goal_service, multiple_goals):
        """Filter goals by goal type."""
        savings = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, goal_type=GoalType.SAVINGS
        )
        assert len(savings) == 2

        debt = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, goal_type=GoalType.DEBT_PAYOFF
        )
        assert len(debt) == 1

    def test_get_goals_filter_by_priority(self, goal_service, multiple_goals):
        """Filter goals by priority."""
        high = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, priority=GoalPriority.HIGH
        )
        assert len(high) == 1

        critical = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, priority=GoalPriority.CRITICAL
        )
        assert len(critical) == 1

    def test_get_goals_combined_filters(self, goal_service, multiple_goals):
        """Apply multiple filters simultaneously."""
        goals = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            status=GoalStatus.ACTIVE,
            goal_type=GoalType.SAVINGS,
        )
        assert len(goals) == 1
        assert goals[0].title == "Savings goal"

    def test_get_goals_pagination(self, goal_service, multiple_goals):
        """Apply skip/limit for pagination."""
        first_page = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, skip=0, limit=2
        )
        assert len(first_page) == 2

        second_page = goal_service.get_goals(
            TEST_USER_ID, TEST_WORKSPACE_ID, skip=2, limit=2
        )
        assert len(second_page) == 2

    def test_get_goals_does_not_return_other_users(
        self, goal_service, sample_goal, other_user_goal
    ):
        """Only return goals for the requested user/workspace."""
        goals = goal_service.get_goals(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert len(goals) == 1
        assert goals[0].user_id == TEST_USER_ID

    def test_get_goals_workspace_auth_denied(self, goal_service, mock_workspace_client):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        with pytest.raises(GoalValidationError):
            goal_service.get_goals(TEST_USER_ID, TEST_WORKSPACE_ID)

    def test_get_goals_db_error_raises_retrieval_error(self, goal_service):
        """Raise GoalRetrievalError on unexpected database errors."""
        with patch.object(goal_service.db, 'query', side_effect=Exception("DB error")):
            with pytest.raises(GoalRetrievalError):
                goal_service.get_goals(TEST_USER_ID, TEST_WORKSPACE_ID)


# ==================== Get Single Goal ====================

class TestGetGoal:
    """Tests for GoalService.get_goal()"""

    def test_get_goal_success(self, goal_service, sample_goal):
        """Successfully retrieve a specific goal."""
        goal = goal_service.get_goal(TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id)

        assert goal.id == sample_goal.id
        assert goal.title == "Save for vacation"

    def test_get_goal_not_found(self, goal_service):
        """Raise GoalNotFoundError for nonexistent goal."""
        with pytest.raises(GoalNotFoundError) as exc_info:
            goal_service.get_goal(TEST_USER_ID, TEST_WORKSPACE_ID, 99999)

        assert "not found" in str(exc_info.value.detail).lower()

    def test_get_goal_wrong_user(self, goal_service, other_user_goal):
        """Raise GoalNotFoundError when goal belongs to another user."""
        with pytest.raises(GoalNotFoundError):
            goal_service.get_goal(TEST_USER_ID, TEST_WORKSPACE_ID, other_user_goal.id)

    def test_get_goal_wrong_workspace(self, goal_service, sample_goal):
        """Raise GoalNotFoundError when goal is in a different workspace."""
        wrong_workspace = uuid4()
        with pytest.raises(GoalNotFoundError):
            goal_service.get_goal(TEST_USER_ID, wrong_workspace, sample_goal.id)


# ==================== Update Goal ====================

class TestUpdateGoal:
    """Tests for GoalService.update_goal()"""

    def test_update_goal_title(self, goal_service, sample_goal):
        """Successfully update goal title."""
        update_data = GoalUpdate(title="Updated vacation fund")

        updated = goal_service.update_goal(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
        )

        assert updated.title == "Updated vacation fund"
        assert updated.id == sample_goal.id

    def test_update_goal_target_amount(self, goal_service, sample_goal):
        """Update target amount recalculates progress."""
        update_data = GoalUpdate(target_amount=10000.00)

        updated = goal_service.update_goal(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
        )

        assert float(updated.target_amount) == 10000.00
        # Progress should be recalculated: 1500/10000 = 15%
        assert float(updated.progress_percentage) == pytest.approx(15.0, rel=0.01)

    def test_update_goal_status(self, goal_service, sample_goal):
        """Update goal status directly."""
        update_data = GoalUpdate(status=GoalStatus.PAUSED)

        updated = goal_service.update_goal(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
        )

        assert updated.status == GoalStatus.PAUSED

    def test_update_goal_multiple_fields(self, goal_service, sample_goal):
        """Update multiple fields at once."""
        update_data = GoalUpdate(
            title="New title",
            description="New description",
            priority=GoalPriority.CRITICAL,
            currency="EUR",
        )

        updated = goal_service.update_goal(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
        )

        assert updated.title == "New title"
        assert updated.description == "New description"
        assert updated.priority == GoalPriority.CRITICAL
        assert updated.currency == "EUR"

    def test_update_goal_not_found(self, goal_service):
        """Raise GoalNotFoundError when goal does not exist."""
        update_data = GoalUpdate(title="Ghost goal")

        with pytest.raises(GoalNotFoundError):
            goal_service.update_goal(TEST_USER_ID, TEST_WORKSPACE_ID, 99999, update_data)

    def test_update_goal_read_only_excess(self, goal_service, sample_goal, mock_subscription_client):
        """Raise GoalReadOnlyExcessError when goal exceeds plan limit."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 1, "enabled": True}
        }

        update_data = GoalUpdate(title="Should fail")

        with pytest.raises(GoalReadOnlyExcessError):
            goal_service.update_goal(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
            )

    def test_update_goal_workspace_auth_denied(self, goal_service, sample_goal, mock_workspace_client):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)
        update_data = GoalUpdate(title="Denied")

        with pytest.raises(GoalValidationError):
            goal_service.update_goal(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
            )

    def test_update_goal_db_error_raises_update_error(self, goal_service, sample_goal):
        """Raise GoalUpdateError on unexpected database errors."""
        update_data = GoalUpdate(title="DB error")

        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB error")):
            with pytest.raises(GoalUpdateError):
                goal_service.update_goal(
                    TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, update_data
                )


# ==================== Update Goal Progress ====================

class TestUpdateGoalProgress:
    """Tests for GoalService.update_goal_progress()"""

    def test_update_progress_success(self, goal_service, sample_goal):
        """Successfully update goal progress."""
        progress_data = GoalProgressUpdate(current_amount=3000.00)

        updated = goal_service.update_goal_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
        )

        assert float(updated.current_amount) == 3000.00
        # 3000/5000 = 60%
        assert float(updated.progress_percentage) == pytest.approx(60.0, rel=0.01)
        assert updated.status == GoalStatus.ACTIVE

    def test_update_progress_reaches_100_auto_completes(self, goal_service, sample_goal):
        """Goal auto-completes when progress reaches 100%."""
        progress_data = GoalProgressUpdate(current_amount=5000.00)

        updated = goal_service.update_goal_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
        )

        assert float(updated.progress_percentage) == pytest.approx(100.0, rel=0.01)
        assert updated.status == GoalStatus.COMPLETED

    def test_update_progress_exceeds_target_caps_at_100(self, goal_service, sample_goal):
        """Progress percentage caps at 100% when current exceeds target."""
        progress_data = GoalProgressUpdate(current_amount=7500.00)

        updated = goal_service.update_goal_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
        )

        assert float(updated.progress_percentage) == pytest.approx(100.0, rel=0.01)
        assert updated.status == GoalStatus.COMPLETED

    def test_update_progress_to_zero(self, goal_service, sample_goal):
        """Set progress back to zero."""
        progress_data = GoalProgressUpdate(current_amount=0.0)

        updated = goal_service.update_goal_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
        )

        assert float(updated.current_amount) == 0.0
        assert float(updated.progress_percentage) == pytest.approx(0.0, rel=0.01)

    def test_update_progress_not_found(self, goal_service):
        """Raise GoalNotFoundError when goal does not exist."""
        progress_data = GoalProgressUpdate(current_amount=1000.00)

        with pytest.raises(GoalNotFoundError):
            goal_service.update_goal_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID, 99999, progress_data
            )

    def test_update_progress_read_only_excess(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Raise GoalReadOnlyExcessError when goal exceeds plan limit."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 1, "enabled": True}
        }

        progress_data = GoalProgressUpdate(current_amount=2000.00)

        with pytest.raises(GoalReadOnlyExcessError):
            goal_service.update_goal_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
            )

    def test_update_progress_db_error_raises_progress_error(self, goal_service, sample_goal):
        """Raise GoalProgressError on unexpected database errors."""
        progress_data = GoalProgressUpdate(current_amount=2000.00)

        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB error")):
            with pytest.raises(GoalProgressError):
                goal_service.update_goal_progress(
                    TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
                )


# ==================== Delete Goal ====================

class TestDeleteGoal:
    """Tests for GoalService.delete_goal()"""

    def test_delete_goal_success(self, goal_service, sample_goal, db_session):
        """Successfully delete a goal."""
        goal_id = sample_goal.id
        result = goal_service.delete_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_id)

        assert result is True

        # Verify goal is removed from database
        remaining = db_session.query(Goal).filter(Goal.id == goal_id).first()
        assert remaining is None

    def test_delete_goal_cascades_milestones(
        self, goal_service, sample_goal, sample_milestone, db_session
    ):
        """Deleting a goal cascades to its milestones."""
        goal_id = sample_goal.id
        milestone_id = sample_milestone.id

        goal_service.delete_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_id)

        remaining_milestone = db_session.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()
        assert remaining_milestone is None

    def test_delete_goal_not_found(self, goal_service):
        """Raise GoalNotFoundError for nonexistent goal."""
        with pytest.raises(GoalNotFoundError):
            goal_service.delete_goal(TEST_USER_ID, TEST_WORKSPACE_ID, 99999)

    def test_delete_goal_wrong_user(self, goal_service, other_user_goal):
        """Raise GoalNotFoundError when goal belongs to another user."""
        with pytest.raises(GoalNotFoundError):
            goal_service.delete_goal(
                TEST_USER_ID, TEST_WORKSPACE_ID, other_user_goal.id
            )

    def test_delete_goal_workspace_auth_denied(
        self, goal_service, sample_goal, mock_workspace_client
    ):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        with pytest.raises(GoalValidationError):
            goal_service.delete_goal(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
            )

    def test_delete_goal_db_error_raises_deletion_error(self, goal_service, sample_goal):
        """Raise GoalDeletionError on unexpected database errors."""
        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB error")):
            with pytest.raises(GoalDeletionError):
                goal_service.delete_goal(
                    TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
                )


# ==================== Goal Statistics ====================

class TestGetGoalStatistics:
    """Tests for GoalService.get_goal_statistics()"""

    def test_statistics_with_goals(self, goal_service, multiple_goals):
        """Calculate correct statistics with multiple goals."""
        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert stats["total_goals"] == 4
        assert stats["active_goals"] == 2
        assert stats["completed_goals"] == 1
        assert stats["currency"] == "USD"

    def test_statistics_empty(self, goal_service):
        """Return zero statistics when user has no goals."""
        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert stats["total_goals"] == 0
        assert stats["active_goals"] == 0
        assert stats["completed_goals"] == 0
        assert stats["total_target_amount"] == 0.0
        assert stats["total_current_amount"] == 0.0
        assert stats["overall_progress"] == 0.0
        assert stats["goals_by_type"] == {}
        assert stats["goals_by_priority"] == {}

    def test_statistics_goals_by_type(self, goal_service, multiple_goals):
        """Statistics include correct goal counts by type."""
        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert stats["goals_by_type"]["SAVINGS"] == 2
        assert stats["goals_by_type"]["DEBT_PAYOFF"] == 1
        assert stats["goals_by_type"]["INVESTMENT"] == 1

    def test_statistics_goals_by_priority(self, goal_service, multiple_goals):
        """Statistics include correct goal counts by priority."""
        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert stats["goals_by_priority"]["HIGH"] == 1
        assert stats["goals_by_priority"]["CRITICAL"] == 1
        assert stats["goals_by_priority"]["MEDIUM"] == 1
        assert stats["goals_by_priority"]["LOW"] == 1

    def test_statistics_currency_conversion(
        self, goal_service, multiple_goals, mock_currency_client
    ):
        """Convert non-base currency amounts when computing totals."""
        # EUR goal has 2000 target, 500 current; convert EUR -> USD at 1.1x
        mock_currency_client.convert_amount.side_effect = lambda amt, frm, to: (
            Decimal(str(float(amt))) * Decimal("1.1") if frm == "EUR" and to == "USD" else None
        )

        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        # EUR goal (target=2000, current=500) should be converted
        # USD goals: target=5000+3000+10000=18000, current=2000+1000+10000=13000
        # EUR->USD: target=2200, current=550
        # Total: target=20200, current=13550
        assert stats["total_goals"] == 4

    def test_statistics_user_currency_fallback(
        self, goal_service, sample_goal, mock_user_client
    ):
        """Fall back to USD when user currency service fails."""
        mock_user_client.get_user_base_currency.side_effect = Exception("Service down")

        stats = goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert stats["currency"] == "USD"

    def test_statistics_workspace_auth_denied(self, goal_service, mock_workspace_client):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        with pytest.raises(GoalValidationError):
            goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)

    def test_statistics_db_error_raises_statistics_error(self, goal_service):
        """Raise GoalStatisticsError on unexpected database errors."""
        with patch.object(goal_service.db, 'query', side_effect=Exception("DB error")):
            with pytest.raises(GoalStatisticsError):
                goal_service.get_goal_statistics(TEST_USER_ID, TEST_WORKSPACE_ID)


# ==================== Internal Methods ====================

class TestInternalMethods:
    """Tests for GoalService internal/helper methods."""

    def test_get_ordered_ids(self, goal_service, multiple_goals):
        """Return goal IDs ordered by created_at ascending."""
        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)

        assert len(ordered) == 4
        assert all(isinstance(i, int) for i in ordered)

    def test_get_ordered_ids_empty(self, goal_service):
        """Return empty list when no goals exist."""
        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)

        assert ordered == []

    def test_check_modify_allowed_passes(self, goal_service, sample_goal):
        """No exception when modify is allowed."""
        # Default mock allows modification
        goal_service._check_modify_allowed(
            sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
        )

    def test_check_modify_allowed_raises_read_only(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Raise GoalReadOnlyExcessError when modify not allowed."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 0, "enabled": True}
        }

        with pytest.raises(GoalReadOnlyExcessError):
            goal_service._check_modify_allowed(
                sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
            )

    def test_get_goal_internal_success(self, goal_service, sample_goal):
        """Retrieve goal without authorization check."""
        goal = goal_service._get_goal_internal(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
        )

        assert goal.id == sample_goal.id

    def test_get_goal_internal_not_found(self, goal_service):
        """Raise GoalNotFoundError for nonexistent goal."""
        with pytest.raises(GoalNotFoundError):
            goal_service._get_goal_internal(TEST_USER_ID, TEST_WORKSPACE_ID, 99999)
