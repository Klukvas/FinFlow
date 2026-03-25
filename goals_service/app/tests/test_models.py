"""
Unit tests for Goal and Milestone models.

Tests cover:
- Goal.calculate_progress() method
- Goal.update_progress() method (progress + auto-complete)
- Milestone.calculate_progress() method
- Milestone.update_progress() method (progress + auto-complete)
- Edge cases for progress calculations
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models.goal import Goal, GoalType, GoalStatus, GoalPriority
from app.models.milestone import Milestone
from app.tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID


class TestGoalCalculateProgress:
    """Tests for Goal.calculate_progress()"""

    def test_calculate_progress_normal(self):
        """Calculate correct percentage for normal values."""
        goal = Goal(
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        )

        progress = goal.calculate_progress()

        assert progress == pytest.approx(25.0, rel=0.01)

    def test_calculate_progress_zero_current(self):
        """Return 0% when no progress made."""
        goal = Goal(
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("0.00"),
        )

        assert goal.calculate_progress() == pytest.approx(0.0)

    def test_calculate_progress_full(self):
        """Return 100% when target reached."""
        goal = Goal(
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("5000.00"),
        )

        assert goal.calculate_progress() == pytest.approx(100.0)

    def test_calculate_progress_exceeds_target(self):
        """Cap at 100% when current exceeds target."""
        goal = Goal(
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("7500.00"),
        )

        assert goal.calculate_progress() == pytest.approx(100.0)

    def test_calculate_progress_zero_target(self):
        """Return 0% when target is zero (prevent division by zero)."""
        goal = Goal(
            target_amount=Decimal("0.00"),
            current_amount=Decimal("100.00"),
        )

        assert goal.calculate_progress() == 0.0

    def test_calculate_progress_negative_target(self):
        """Return 0% when target is negative."""
        goal = Goal(
            target_amount=Decimal("-100.00"),
            current_amount=Decimal("50.00"),
        )

        assert goal.calculate_progress() == 0.0

    def test_calculate_progress_small_amounts(self):
        """Handle small decimal amounts correctly."""
        goal = Goal(
            target_amount=Decimal("0.50"),
            current_amount=Decimal("0.25"),
        )

        assert goal.calculate_progress() == pytest.approx(50.0, rel=0.01)

    def test_calculate_progress_large_amounts(self):
        """Handle large amounts correctly."""
        goal = Goal(
            target_amount=Decimal("999999999.99"),
            current_amount=Decimal("500000000.00"),
        )

        expected = 500000000.00 / 999999999.99 * 100
        assert goal.calculate_progress() == pytest.approx(expected, rel=0.001)


class TestGoalUpdateProgress:
    """Tests for Goal.update_progress()"""

    def test_update_progress_sets_percentage(self):
        """Update progress_percentage based on current/target."""
        goal = Goal(
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("3000.00"),
            status=GoalStatus.ACTIVE,
        )

        goal.update_progress()

        assert float(goal.progress_percentage) == pytest.approx(30.0, rel=0.01)
        assert goal.status == GoalStatus.ACTIVE

    def test_update_progress_auto_completes_at_100(self):
        """Auto-complete goal when progress reaches 100%."""
        goal = Goal(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            status=GoalStatus.ACTIVE,
        )

        goal.update_progress()

        assert float(goal.progress_percentage) == pytest.approx(100.0)
        assert goal.status == GoalStatus.COMPLETED

    def test_update_progress_auto_completes_when_exceeding(self):
        """Auto-complete goal when current exceeds target."""
        goal = Goal(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1500.00"),
            status=GoalStatus.ACTIVE,
        )

        goal.update_progress()

        assert goal.status == GoalStatus.COMPLETED

    def test_update_progress_does_not_complete_paused(self):
        """Do not auto-complete paused goals even at 100%."""
        goal = Goal(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            status=GoalStatus.PAUSED,
        )

        goal.update_progress()

        assert goal.status == GoalStatus.PAUSED

    def test_update_progress_does_not_complete_cancelled(self):
        """Do not auto-complete cancelled goals even at 100%."""
        goal = Goal(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            status=GoalStatus.CANCELLED,
        )

        goal.update_progress()

        assert goal.status == GoalStatus.CANCELLED

    def test_update_progress_already_completed(self):
        """Already completed goal stays completed."""
        goal = Goal(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            status=GoalStatus.COMPLETED,
        )

        goal.update_progress()

        assert goal.status == GoalStatus.COMPLETED


class TestMilestoneCalculateProgress:
    """Tests for Milestone.calculate_progress()"""

    def test_calculate_progress_normal(self):
        """Calculate correct percentage for normal values."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("400.00"),
        )

        assert milestone.calculate_progress() == pytest.approx(40.0, rel=0.01)

    def test_calculate_progress_zero_current(self):
        """Return 0% when no progress."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("0.00"),
        )

        assert milestone.calculate_progress() == pytest.approx(0.0)

    def test_calculate_progress_full(self):
        """Return 100% when target reached."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
        )

        assert milestone.calculate_progress() == pytest.approx(100.0)

    def test_calculate_progress_exceeds_target(self):
        """Cap at 100% when current exceeds target."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1500.00"),
        )

        assert milestone.calculate_progress() == pytest.approx(100.0)

    def test_calculate_progress_zero_target(self):
        """Return 0% when target is zero."""
        milestone = Milestone(
            target_amount=Decimal("0.00"),
            current_amount=Decimal("100.00"),
        )

        assert milestone.calculate_progress() == 0.0

    def test_calculate_progress_negative_target(self):
        """Return 0% when target is negative."""
        milestone = Milestone(
            target_amount=Decimal("-50.00"),
            current_amount=Decimal("25.00"),
        )

        assert milestone.calculate_progress() == 0.0


class TestMilestoneUpdateProgress:
    """Tests for Milestone.update_progress()"""

    def test_update_progress_not_complete(self):
        """Milestone stays incomplete when under target."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("500.00"),
            is_completed=False,
        )

        milestone.update_progress()

        assert milestone.is_completed is False

    def test_update_progress_completes_at_100(self):
        """Auto-complete milestone when progress reaches 100%."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            is_completed=False,
        )

        milestone.update_progress()

        assert milestone.is_completed is True
        assert milestone.completed_at is not None

    def test_update_progress_completes_when_exceeding(self):
        """Auto-complete milestone when current exceeds target."""
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1500.00"),
            is_completed=False,
        )

        milestone.update_progress()

        assert milestone.is_completed is True

    def test_update_progress_already_completed_no_change(self):
        """Already completed milestone stays completed."""
        completed_at = datetime.now(timezone.utc)
        milestone = Milestone(
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            is_completed=True,
            completed_at=completed_at,
        )

        milestone.update_progress()

        assert milestone.is_completed is True
        # completed_at should not change
        assert milestone.completed_at == completed_at


class TestGoalModel:
    """Tests for Goal model attributes and relationships."""

    def test_goal_creates_in_db(self, db_session):
        """Goal persists in database with all fields."""
        goal = Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test goal",
            description="Test description",
            goal_type=GoalType.SAVINGS,
            priority=GoalPriority.HIGH,
            status=GoalStatus.ACTIVE,
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("1000.00"),
            currency="EUR",
            progress_percentage=Decimal("20.0"),
            is_milestone_based=True,
            start_date=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)

        assert goal.id is not None
        assert goal.title == "Test goal"
        assert goal.goal_type == GoalType.SAVINGS
        assert goal.currency == "EUR"

    def test_goal_milestone_cascade_delete(self, db_session):
        """Deleting a goal cascades to its milestones."""
        goal = Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Cascade test",
            goal_type=GoalType.SAVINGS,
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("0.00"),
            currency="USD",
            start_date=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)

        milestone = Milestone(
            goal_id=goal.id,
            title="Child milestone",
            target_amount=Decimal("500.00"),
            current_amount=Decimal("0.00"),
        )
        db_session.add(milestone)
        db_session.commit()
        milestone_id = milestone.id

        db_session.delete(goal)
        db_session.commit()

        remaining = db_session.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()
        assert remaining is None


class TestMilestoneModel:
    """Tests for Milestone model attributes."""

    def test_milestone_creates_in_db(self, db_session):
        """Milestone persists in database with all fields."""
        goal = Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Parent goal",
            goal_type=GoalType.SAVINGS,
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("0.00"),
            currency="USD",
            start_date=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)

        milestone = Milestone(
            goal_id=goal.id,
            title="First milestone",
            description="Reach $1000",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("250.00"),
            is_completed=False,
            order_index=0,
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.id is not None
        assert milestone.goal_id == goal.id
        assert milestone.title == "First milestone"
        assert float(milestone.target_amount) == 1000.00

    def test_milestone_goal_relationship(self, db_session):
        """Milestone has backref to parent goal."""
        goal = Goal(
            user_id=TEST_USER_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Parent",
            goal_type=GoalType.SAVINGS,
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("0.00"),
            currency="USD",
            start_date=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)

        milestone = Milestone(
            goal_id=goal.id,
            title="Child",
            target_amount=Decimal("500.00"),
            current_amount=Decimal("0.00"),
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.goal.id == goal.id
        assert len(goal.milestones) == 1
        assert goal.milestones[0].id == milestone.id
