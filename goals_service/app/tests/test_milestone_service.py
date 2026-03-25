"""
Unit tests for GoalService - Milestone Operations.

Tests cover:
- Milestone CRUD operations
- Milestone progress tracking
- Goal-milestone relationship
- Error handling for milestones
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch

from app.services.goal import GoalService
from app.models.goal import Goal, GoalType, GoalStatus
from app.models.milestone import Milestone
from app.schemas.goal import MilestoneCreate, MilestoneProgressUpdate
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError,
    MilestoneNotFoundError, MilestoneCreationError,
    MilestoneRetrievalError, MilestoneProgressUpdateError,
)

from app.tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID


# ==================== Create Milestone ====================

class TestCreateMilestone:
    """Tests for GoalService.create_milestone()"""

    def test_create_milestone_success(self, goal_service, sample_goal):
        """Successfully create a milestone for a goal."""
        milestone_data = MilestoneCreate(
            title="First $1000",
            description="Save first thousand dollars",
            target_amount=1000.00,
            order_index=0,
        )

        milestone = goal_service.create_milestone(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
        )

        assert milestone.id is not None
        assert milestone.title == "First $1000"
        assert milestone.description == "Save first thousand dollars"
        assert float(milestone.target_amount) == 1000.00
        assert milestone.goal_id == sample_goal.id
        assert milestone.order_index == 0
        assert milestone.is_completed is False

    def test_create_milestone_default_values(self, goal_service, sample_goal):
        """Milestone uses correct defaults when optional fields omitted."""
        milestone_data = MilestoneCreate(
            title="Simple milestone",
            target_amount=500.00,
        )

        milestone = goal_service.create_milestone(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
        )

        assert milestone.description is None
        assert milestone.order_index == 0
        assert float(milestone.current_amount) == 0.0

    def test_create_milestone_goal_not_found(self, goal_service):
        """Raise GoalNotFoundError when parent goal does not exist."""
        milestone_data = MilestoneCreate(
            title="Orphan milestone",
            target_amount=100.00,
        )

        with pytest.raises(GoalNotFoundError):
            goal_service.create_milestone(
                TEST_USER_ID, TEST_WORKSPACE_ID, 99999, milestone_data
            )

    def test_create_milestone_wrong_user_goal(self, goal_service, other_user_goal):
        """Raise GoalNotFoundError when goal belongs to another user."""
        milestone_data = MilestoneCreate(
            title="Should fail",
            target_amount=100.00,
        )

        with pytest.raises(GoalNotFoundError):
            goal_service.create_milestone(
                TEST_USER_ID, TEST_WORKSPACE_ID, other_user_goal.id, milestone_data
            )

    def test_create_milestone_workspace_auth_denied(
        self, goal_service, sample_goal, mock_workspace_client
    ):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        milestone_data = MilestoneCreate(
            title="Denied milestone",
            target_amount=100.00,
        )

        with pytest.raises(GoalValidationError):
            goal_service.create_milestone(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
            )

    def test_create_multiple_milestones_ordered(self, goal_service, sample_goal):
        """Create multiple milestones with different order indexes."""
        for i in range(3):
            milestone_data = MilestoneCreate(
                title=f"Milestone {i + 1}",
                target_amount=1000.00 * (i + 1),
                order_index=i,
            )
            milestone = goal_service.create_milestone(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
            )
            assert milestone.order_index == i

    def test_create_milestone_db_error_raises_creation_error(
        self, goal_service, sample_goal
    ):
        """Raise MilestoneCreationError on unexpected database errors."""
        milestone_data = MilestoneCreate(
            title="DB error milestone",
            target_amount=100.00,
        )

        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB error")):
            with pytest.raises(MilestoneCreationError):
                goal_service.create_milestone(
                    TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
                )


# ==================== Get Milestones ====================

class TestGetMilestones:
    """Tests for GoalService.get_milestones()"""

    def test_get_milestones_success(self, goal_service, sample_goal, multiple_milestones):
        """Return milestones for a goal ordered by order_index."""
        milestones = goal_service.get_milestones(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
        )

        assert len(milestones) == 3
        # Verify ordering
        assert milestones[0].order_index == 0
        assert milestones[1].order_index == 1
        assert milestones[2].order_index == 2

    def test_get_milestones_empty(self, goal_service, sample_goal):
        """Return empty list when goal has no milestones."""
        milestones = goal_service.get_milestones(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
        )

        assert milestones == []

    def test_get_milestones_goal_not_found(self, goal_service):
        """Raise GoalNotFoundError when parent goal does not exist."""
        with pytest.raises(GoalNotFoundError):
            goal_service.get_milestones(TEST_USER_ID, TEST_WORKSPACE_ID, 99999)

    def test_get_milestones_wrong_user(self, goal_service, other_user_goal):
        """Raise GoalNotFoundError when goal belongs to another user."""
        with pytest.raises(GoalNotFoundError):
            goal_service.get_milestones(
                TEST_USER_ID, TEST_WORKSPACE_ID, other_user_goal.id
            )

    def test_get_milestones_workspace_auth_denied(
        self, goal_service, sample_goal, mock_workspace_client
    ):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        with pytest.raises(GoalValidationError):
            goal_service.get_milestones(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
            )

    def test_get_milestones_db_error_raises_retrieval_error(
        self, goal_service, sample_goal
    ):
        """Raise MilestoneRetrievalError on unexpected database errors."""
        # Need to let the first query (goal lookup) succeed, but fail on milestones
        original_query = goal_service.db.query
        call_count = [0]

        def side_effect_query(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise Exception("DB error on milestones")
            return original_query(*args, **kwargs)

        with patch.object(goal_service.db, 'query', side_effect=side_effect_query):
            with pytest.raises(MilestoneRetrievalError):
                goal_service.get_milestones(
                    TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id
                )


# ==================== Update Milestone Progress ====================

class TestUpdateMilestoneProgress:
    """Tests for GoalService.update_milestone_progress()"""

    def test_update_milestone_progress_success(
        self, goal_service, sample_goal, sample_milestone
    ):
        """Successfully update milestone progress."""
        progress_data = MilestoneProgressUpdate(current_amount=750.00)

        updated = goal_service.update_milestone_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            sample_goal.id, sample_milestone.id, progress_data
        )

        assert float(updated.current_amount) == 750.00
        assert updated.is_completed is False

    def test_update_milestone_progress_completes(
        self, goal_service, sample_goal, sample_milestone
    ):
        """Milestone auto-completes when progress reaches 100%."""
        progress_data = MilestoneProgressUpdate(current_amount=1000.00)

        updated = goal_service.update_milestone_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            sample_goal.id, sample_milestone.id, progress_data
        )

        assert float(updated.current_amount) == 1000.00
        assert updated.is_completed is True

    def test_update_milestone_progress_exceeds_target(
        self, goal_service, sample_goal, sample_milestone
    ):
        """Milestone completes when current exceeds target."""
        progress_data = MilestoneProgressUpdate(current_amount=1500.00)

        updated = goal_service.update_milestone_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            sample_goal.id, sample_milestone.id, progress_data
        )

        assert updated.is_completed is True

    def test_update_milestone_progress_to_zero(
        self, goal_service, sample_goal, sample_milestone
    ):
        """Reset milestone progress to zero."""
        progress_data = MilestoneProgressUpdate(current_amount=0.0)

        updated = goal_service.update_milestone_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            sample_goal.id, sample_milestone.id, progress_data
        )

        assert float(updated.current_amount) == 0.0
        assert updated.is_completed is False

    def test_update_milestone_not_found(self, goal_service, sample_goal):
        """Raise MilestoneNotFoundError when milestone does not exist."""
        progress_data = MilestoneProgressUpdate(current_amount=100.00)

        with pytest.raises(MilestoneNotFoundError) as exc_info:
            goal_service.update_milestone_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID,
                sample_goal.id, 99999, progress_data
            )

        assert "not found" in str(exc_info.value.detail).lower()

    def test_update_milestone_wrong_goal(
        self, goal_service, sample_goal, sample_milestone, db_session
    ):
        """Raise error when milestone does not belong to the specified goal."""
        # Create another goal
        other_goal = Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Other goal",
            goal_type=GoalType.SAVINGS,
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("0.00"),
            currency="USD",
            start_date=datetime.now(timezone.utc),
        )
        db_session.add(other_goal)
        db_session.commit()
        db_session.refresh(other_goal)

        progress_data = MilestoneProgressUpdate(current_amount=100.00)

        with pytest.raises(MilestoneNotFoundError):
            goal_service.update_milestone_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID,
                other_goal.id, sample_milestone.id, progress_data
            )

    def test_update_milestone_goal_not_found(self, goal_service, sample_milestone):
        """Raise GoalNotFoundError when parent goal does not exist."""
        progress_data = MilestoneProgressUpdate(current_amount=100.00)

        with pytest.raises(GoalNotFoundError):
            goal_service.update_milestone_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID,
                99999, sample_milestone.id, progress_data
            )

    def test_update_milestone_workspace_auth_denied(
        self, goal_service, sample_goal, sample_milestone, mock_workspace_client
    ):
        """Raise GoalValidationError when workspace access denied."""
        mock_workspace_client.authorize.return_value = (False, None)

        progress_data = MilestoneProgressUpdate(current_amount=100.00)

        with pytest.raises(GoalValidationError):
            goal_service.update_milestone_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID,
                sample_goal.id, sample_milestone.id, progress_data
            )

    def test_update_milestone_db_error_raises_progress_error(
        self, goal_service, sample_goal, sample_milestone
    ):
        """Raise MilestoneProgressUpdateError on unexpected database errors."""
        progress_data = MilestoneProgressUpdate(current_amount=500.00)

        with patch.object(goal_service.db, 'commit', side_effect=Exception("DB error")):
            with pytest.raises(MilestoneProgressUpdateError):
                goal_service.update_milestone_progress(
                    TEST_USER_ID, TEST_WORKSPACE_ID,
                    sample_goal.id, sample_milestone.id, progress_data
                )
