"""
Tests for read-only excess behavior in goals_service.

Covers:
- get_read_only_ids returning correct IDs when over limit
- Update progress on a read-only goal (blocked by _check_modify_allowed)
- Create milestone on a read-only goal (allowed -- no _check_modify_allowed)
- Full flow: create goals -> limit drops -> verify read-only flags
- _check_modify_allowed blocking updates on excess goals
- _check_modify_allowed allowing updates on within-limit goals
- _get_ordered_ids correctness for read-only computation
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.services.goal import GoalService
from app.models.goal import Goal, GoalType, GoalStatus, GoalPriority
from app.models.milestone import Milestone
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalProgressUpdate,
    MilestoneCreate, MilestoneProgressUpdate,
)
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalReadOnlyExcessError,
)

from app.tests.conftest import TEST_USER_ID, OTHER_USER_ID, TEST_WORKSPACE_ID


# ==================== get_read_only_ids returning correct IDs ====================


class TestGetReadOnlyIdsInListEndpoint:
    """Tests for read-only flag marking in the GET /api/v1/goals/ router."""

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_goals_marked_read_only_when_over_limit(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """Goals beyond the plan limit are flagged is_read_only=True."""
        ids = [10, 20, 30]

        mock_goals = []
        for gid in ids:
            mg = MagicMock()
            mg.id = gid
            mg.user_id = TEST_USER_ID
            mg.workspace_id = TEST_WORKSPACE_ID
            mg.title = f"Goal {gid}"
            mg.description = None
            mg.goal_type = GoalType.SAVINGS
            mg.priority = GoalPriority.MEDIUM
            mg.status = GoalStatus.ACTIVE
            mg.target_amount = 1000.00
            mg.current_amount = 500.00
            mg.currency = "USD"
            mg.progress_percentage = 50.0
            mg.is_milestone_based = False
            mg.target_date = None
            mg.start_date = datetime.now(timezone.utc)
            mg.created_at = datetime.now(timezone.utc)
            mg.updated_at = None
            mock_goals.append(mg)

        mock_get.return_value = mock_goals
        mock_ordered.return_value = ids

        mock_sub_client = MagicMock()
        # limit=2 -> 3rd goal (id=30) is read-only
        mock_sub_client.get_read_only_ids.return_value = {30}
        mock_sub_instance.return_value = mock_sub_client

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 3

        ro_flags = {item["id"]: item["is_read_only"] for item in items}
        assert ro_flags[10] is False
        assert ro_flags[20] is False
        assert ro_flags[30] is True

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_no_goals_marked_read_only_within_limit(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """All goals are editable when count is within plan limit."""
        mock_get.return_value = []
        mock_ordered.return_value = []

        mock_sub_client = MagicMock()
        mock_sub_client.get_read_only_ids.return_value = set()
        mock_sub_instance.return_value = mock_sub_client

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 200
        items = response.json()["items"]
        assert all(item.get("is_read_only", False) is False for item in items)

    @patch("app.services.goal.GoalService.get_goals")
    @patch("app.services.goal.GoalService._get_ordered_ids")
    @patch("app.services.goal.SubscriptionClient.get_instance")
    def test_all_goals_read_only_when_limit_zero(
        self, mock_sub_instance, mock_ordered, mock_get, client, auth_headers
    ):
        """When plan limit is 0, every goal is read-only."""
        ids = [1, 2]
        mock_goals = []
        for gid in ids:
            mg = MagicMock()
            mg.id = gid
            mg.user_id = TEST_USER_ID
            mg.workspace_id = TEST_WORKSPACE_ID
            mg.title = f"Goal {gid}"
            mg.description = None
            mg.goal_type = GoalType.SAVINGS
            mg.priority = GoalPriority.MEDIUM
            mg.status = GoalStatus.ACTIVE
            mg.target_amount = 1000.00
            mg.current_amount = 0.00
            mg.currency = "USD"
            mg.progress_percentage = 0.0
            mg.is_milestone_based = False
            mg.target_date = None
            mg.start_date = datetime.now(timezone.utc)
            mg.created_at = datetime.now(timezone.utc)
            mg.updated_at = None
            mock_goals.append(mg)

        mock_get.return_value = mock_goals
        mock_ordered.return_value = ids

        mock_sub_client = MagicMock()
        mock_sub_client.get_read_only_ids.return_value = set(ids)
        mock_sub_instance.return_value = mock_sub_client

        response = client.get("/api/v1/goals/", headers=auth_headers)

        assert response.status_code == 200
        items = response.json()["items"]
        assert all(item["is_read_only"] is True for item in items)


# ==================== Update progress on read-only goal ====================


class TestUpdateProgressOnReadOnlyGoal:
    """Tests for updating progress on goals in the read-only excess zone."""

    def test_update_progress_on_read_only_goal_blocked(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Updating progress on a read-only goal raises GoalReadOnlyExcessError."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 0, "enabled": True}
        }

        progress_data = GoalProgressUpdate(current_amount=3000.00)

        with pytest.raises(GoalReadOnlyExcessError) as exc_info:
            goal_service.update_goal_progress(
                TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
            )

        assert exc_info.value.goal_id == sample_goal.id

    def test_update_progress_on_editable_goal_succeeds(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Updating progress on a goal within limit succeeds."""
        mock_subscription_client.check_modify_allowed.return_value = True

        progress_data = GoalProgressUpdate(current_amount=3000.00)

        updated = goal_service.update_goal_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, progress_data
        )

        assert float(updated.current_amount) == 3000.00


# ==================== Create milestone on read-only goal ====================


class TestCreateMilestoneOnReadOnlyGoal:
    """Tests for creating milestones on goals in the read-only excess zone."""

    def test_create_milestone_on_read_only_goal_succeeds(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Creating a milestone on a read-only goal is allowed.

        The create_milestone method does NOT call _check_modify_allowed,
        so milestones can still be added even on excess goals.
        """
        mock_subscription_client.check_modify_allowed.return_value = False

        milestone_data = MilestoneCreate(
            title="First step",
            target_amount=1000.00,
            order_index=0,
        )

        milestone = goal_service.create_milestone(
            TEST_USER_ID, TEST_WORKSPACE_ID, sample_goal.id, milestone_data
        )

        assert milestone.id is not None
        assert milestone.title == "First step"
        assert milestone.goal_id == sample_goal.id

    def test_update_milestone_progress_on_read_only_goal_succeeds(
        self, goal_service, sample_goal, sample_milestone, mock_subscription_client
    ):
        """Updating milestone progress on a read-only goal is allowed.

        The update_milestone_progress method does NOT call _check_modify_allowed.
        """
        mock_subscription_client.check_modify_allowed.return_value = False

        progress_data = MilestoneProgressUpdate(current_amount=800.00)

        updated = goal_service.update_milestone_progress(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            sample_goal.id, sample_milestone.id, progress_data
        )

        assert float(updated.current_amount) == 800.00


# ==================== Full flow: create -> limit drops -> verify ====================


class TestFullFlowLimitDrop:
    """Full integration flow: create goals, then simulate a plan downgrade."""

    def test_create_goals_then_limit_drops_marks_excess_read_only(
        self, goal_service, db_session, mock_subscription_client
    ):
        """After limit drops, excess goals are identified by _get_ordered_ids."""
        # Create 4 goals
        goal_ids = []
        for i in range(4):
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {i}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
            db_session.flush()
            goal_ids.append(goal.id)
        db_session.commit()

        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)
        assert len(ordered) == 4

        # Simulate limit=2: get_read_only_ids returns IDs beyond index 2
        mock_subscription_client.get_read_only_ids.return_value = set(ordered[2:])

        read_only = mock_subscription_client.get_read_only_ids(
            TEST_USER_ID, "goals", ordered
        )
        assert len(read_only) == 2
        assert ordered[0] not in read_only
        assert ordered[1] not in read_only
        assert ordered[2] in read_only
        assert ordered[3] in read_only

    def test_oldest_goals_remain_editable_after_limit_drop(
        self, goal_service, db_session, mock_subscription_client
    ):
        """The oldest N goals (within limit) stay editable."""
        goal_ids = []
        for i in range(3):
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {i}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
            db_session.flush()
            goal_ids.append(goal.id)
        db_session.commit()

        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)

        # Simulate limit=2: first 2 editable, 3rd read-only
        mock_subscription_client.check_modify_allowed.side_effect = (
            lambda uid, rid, feat, ids: rid in set(ids[:2])
        )

        assert mock_subscription_client.check_modify_allowed(
            TEST_USER_ID, ordered[0], "goals", ordered
        ) is True
        assert mock_subscription_client.check_modify_allowed(
            TEST_USER_ID, ordered[1], "goals", ordered
        ) is True
        assert mock_subscription_client.check_modify_allowed(
            TEST_USER_ID, ordered[2], "goals", ordered
        ) is False

    def test_update_excess_goal_raises_read_only_error(
        self, goal_service, db_session, mock_subscription_client
    ):
        """Updating a goal in the excess zone raises GoalReadOnlyExcessError."""
        goals = []
        for i in range(3):
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {i}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
            db_session.flush()
            goals.append(goal)
        db_session.commit()

        excess_goal = goals[2]

        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 2, "enabled": True}
        }

        update = GoalUpdate(title="Should Fail")

        with pytest.raises(GoalReadOnlyExcessError) as exc_info:
            goal_service.update_goal(
                TEST_USER_ID, TEST_WORKSPACE_ID, excess_goal.id, update
            )

        assert exc_info.value.goal_id == excess_goal.id
        assert exc_info.value.limit == 2

    def test_update_within_limit_goal_succeeds_after_limit_drop(
        self, goal_service, db_session, mock_subscription_client
    ):
        """Updating a goal within the limit still works after limit drops."""
        goals = []
        for i in range(3):
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {i}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
            db_session.flush()
            goals.append(goal)
        db_session.commit()

        mock_subscription_client.check_modify_allowed.return_value = True

        update = GoalUpdate(title="Updated Successfully")
        result = goal_service.update_goal(
            TEST_USER_ID, TEST_WORKSPACE_ID, goals[0].id, update
        )

        assert result.title == "Updated Successfully"


# ==================== Delete read-only goal ====================


class TestDeleteReadOnlyGoal:
    """Tests for deleting a goal that is in the read-only excess zone."""

    def test_delete_read_only_goal_succeeds(
        self, goal_service, sample_goal, db_session, mock_subscription_client
    ):
        """Deleting a read-only (excess) goal is allowed.

        The delete_goal method does NOT call _check_modify_allowed,
        so users can reduce their goal count to get back within limits.
        """
        mock_subscription_client.check_modify_allowed.return_value = False

        goal_id = sample_goal.id
        result = goal_service.delete_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_id)

        assert result is True

        remaining = db_session.query(Goal).filter(Goal.id == goal_id).first()
        assert remaining is None

    def test_delete_read_only_goal_cascades_milestones(
        self, goal_service, sample_goal, sample_milestone, db_session,
        mock_subscription_client
    ):
        """Deleting a read-only goal cascades to its milestones."""
        mock_subscription_client.check_modify_allowed.return_value = False

        goal_id = sample_goal.id
        milestone_id = sample_milestone.id

        goal_service.delete_goal(TEST_USER_ID, TEST_WORKSPACE_ID, goal_id)

        remaining = db_session.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()
        assert remaining is None


# ==================== _check_modify_allowed edge cases ====================


class TestCheckModifyAllowed:
    """Tests for GoalService._check_modify_allowed()."""

    def test_check_modify_allowed_passes_within_limit(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """No exception when the goal is within plan limits."""
        mock_subscription_client.check_modify_allowed.return_value = True

        # Should not raise
        goal_service._check_modify_allowed(
            sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
        )

    def test_check_modify_allowed_raises_for_excess(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """Raises GoalReadOnlyExcessError for excess goals."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {
            "goals": {"limit_value": 0, "enabled": True}
        }

        with pytest.raises(GoalReadOnlyExcessError) as exc_info:
            goal_service._check_modify_allowed(
                sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert exc_info.value.goal_id == sample_goal.id
        assert exc_info.value.limit == 0

    def test_check_modify_allowed_uses_ordered_ids(
        self, goal_service, multiple_goals, mock_subscription_client
    ):
        """_check_modify_allowed passes ordered IDs to subscription client."""
        mock_subscription_client.check_modify_allowed.return_value = True

        first_goal = multiple_goals[0]
        goal_service._check_modify_allowed(
            first_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
        )

        call_args = mock_subscription_client.check_modify_allowed.call_args
        # Args: (user_id, record_id, feature_code, ordered_ids)
        assert call_args[0][0] == TEST_USER_ID
        assert call_args[0][1] == first_goal.id
        assert call_args[0][2] == "goals"
        ordered_ids = call_args[0][3]
        assert len(ordered_ids) == len(multiple_goals)

    def test_check_modify_allowed_features_missing_key_defaults_limit_zero(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """When features dict lacks the 'goals' key, limit defaults to 0."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = {}

        with pytest.raises(GoalReadOnlyExcessError) as exc_info:
            goal_service._check_modify_allowed(
                sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert exc_info.value.limit == 0

    def test_check_modify_allowed_features_returns_none_defaults_limit_zero(
        self, goal_service, sample_goal, mock_subscription_client
    ):
        """When get_user_features returns None, limit defaults to 0."""
        mock_subscription_client.check_modify_allowed.return_value = False
        mock_subscription_client.get_user_features.return_value = None

        with pytest.raises(GoalReadOnlyExcessError) as exc_info:
            goal_service._check_modify_allowed(
                sample_goal.id, TEST_USER_ID, TEST_WORKSPACE_ID
            )

        assert exc_info.value.limit == 0


# ==================== _get_ordered_ids for read-only computation ====================


class TestGetOrderedIdsForReadOnly:
    """Tests confirming _get_ordered_ids produces correct order for read-only computation."""

    def test_ordered_ids_match_creation_order(
        self, goal_service, db_session
    ):
        """IDs are ordered by created_at ASC, then id ASC -- matching creation order."""
        ids = []
        for i in range(5):
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {i}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
            db_session.flush()
            ids.append(goal.id)
        db_session.commit()

        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)

        assert ordered == ids

    def test_ordered_ids_only_for_workspace(
        self, goal_service, db_session
    ):
        """_get_ordered_ids only returns IDs for the specified workspace."""
        ws1 = str(uuid4())
        ws2 = str(uuid4())

        for ws in [ws1, ws1, ws2]:
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=ws,
                title="Goal",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=GoalStatus.ACTIVE,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
        db_session.commit()

        ws1_ids = goal_service._get_ordered_ids(ws1)
        ws2_ids = goal_service._get_ordered_ids(ws2)

        assert len(ws1_ids) == 2
        assert len(ws2_ids) == 1

    def test_ordered_ids_includes_all_statuses(
        self, goal_service, db_session
    ):
        """_get_ordered_ids includes goals of all statuses (active, completed, paused)."""
        for status in [GoalStatus.ACTIVE, GoalStatus.COMPLETED, GoalStatus.PAUSED]:
            goal = Goal(
                user_id=TEST_USER_ID,
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Goal {status.value}",
                goal_type=GoalType.SAVINGS,
                priority=GoalPriority.MEDIUM,
                status=status,
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("0.00"),
                currency="USD",
                progress_percentage=Decimal("0.0"),
                start_date=datetime.now(timezone.utc),
            )
            db_session.add(goal)
        db_session.commit()

        ordered = goal_service._get_ordered_ids(TEST_WORKSPACE_ID)

        assert len(ordered) == 3
