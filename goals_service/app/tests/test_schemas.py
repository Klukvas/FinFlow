"""
Unit tests for Pydantic schemas (input validation).

Tests cover:
- GoalCreate validation
- GoalUpdate validation
- GoalProgressUpdate validation
- MilestoneCreate validation
- MilestoneProgressUpdate validation
- Date parsing
- Amount rounding
"""
import pytest
from datetime import datetime, date
from pydantic import ValidationError

from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalProgressUpdate,
    MilestoneCreate, MilestoneUpdate, MilestoneProgressUpdate,
    GoalResponse, GoalListResponse, GoalStatistics,
)
from app.models.goal import GoalType, GoalStatus, GoalPriority


class TestGoalCreateValidation:
    """Tests for GoalCreate schema validation."""

    def test_valid_minimal(self):
        """Accept minimal valid input."""
        goal = GoalCreate(
            title="Save money",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.00,
        )

        assert goal.title == "Save money"
        assert goal.goal_type == GoalType.SAVINGS
        assert goal.target_amount == 1000.00
        assert goal.priority == GoalPriority.MEDIUM
        assert goal.currency == "USD"
        assert goal.is_milestone_based is False

    def test_valid_all_fields(self):
        """Accept all fields populated."""
        goal = GoalCreate(
            title="Full goal",
            description="All fields set",
            goal_type=GoalType.INVESTMENT,
            priority=GoalPriority.CRITICAL,
            target_amount=50000.00,
            currency="EUR",
            target_date=datetime(2027, 12, 31),
            is_milestone_based=True,
        )

        assert goal.description == "All fields set"
        assert goal.priority == GoalPriority.CRITICAL
        assert goal.currency == "EUR"
        assert goal.is_milestone_based is True

    def test_reject_empty_title(self):
        """Reject empty title."""
        with pytest.raises(ValidationError) as exc_info:
            GoalCreate(
                title="",
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
            )

        assert "title" in str(exc_info.value).lower()

    def test_reject_title_too_long(self):
        """Reject title exceeding 255 characters."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="x" * 256,
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
            )

    def test_reject_missing_title(self):
        """Reject missing title."""
        with pytest.raises(ValidationError):
            GoalCreate(
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
            )

    def test_reject_zero_target_amount(self):
        """Reject zero target amount."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="Zero amount",
                goal_type=GoalType.SAVINGS,
                target_amount=0,
            )

    def test_reject_negative_target_amount(self):
        """Reject negative target amount."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="Negative amount",
                goal_type=GoalType.SAVINGS,
                target_amount=-500,
            )

    def test_target_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        goal = GoalCreate(
            title="Round amount",
            goal_type=GoalType.SAVINGS,
            target_amount=1000.999,
        )

        assert goal.target_amount == 1001.00

    def test_reject_invalid_goal_type(self):
        """Reject invalid goal type string."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="Bad type",
                goal_type="NONEXISTENT",
                target_amount=1000,
            )

    def test_all_goal_types_accepted(self):
        """All defined goal types are accepted."""
        for goal_type in GoalType:
            goal = GoalCreate(
                title=f"Type {goal_type.value}",
                goal_type=goal_type,
                target_amount=1000,
            )
            assert goal.goal_type == goal_type

    def test_all_priorities_accepted(self):
        """All defined priorities are accepted."""
        for priority in GoalPriority:
            goal = GoalCreate(
                title=f"Priority {priority.value}",
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
                priority=priority,
            )
            assert goal.priority == priority

    def test_description_max_length(self):
        """Reject description exceeding 1000 characters."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="Long desc",
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
                description="x" * 1001,
            )

    def test_currency_max_length(self):
        """Reject currency code exceeding 3 characters."""
        with pytest.raises(ValidationError):
            GoalCreate(
                title="Bad currency",
                goal_type=GoalType.SAVINGS,
                target_amount=1000,
                currency="ABCD",
            )


class TestGoalCreateDateParsing:
    """Tests for GoalCreate target_date parsing."""

    def test_parse_date_only_string(self):
        """Parse YYYY-MM-DD string."""
        goal = GoalCreate(
            title="Date test",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date="2027-06-15",
        )

        assert goal.target_date == datetime(2027, 6, 15, 0, 0, 0)

    def test_parse_datetime_string(self):
        """Parse YYYY-MM-DDTHH:MM:SS string."""
        goal = GoalCreate(
            title="Datetime test",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date="2027-06-15T14:30:00",
        )

        assert goal.target_date.year == 2027
        assert goal.target_date.hour == 14
        assert goal.target_date.minute == 30

    def test_parse_datetime_with_space(self):
        """Parse YYYY-MM-DD HH:MM:SS string."""
        goal = GoalCreate(
            title="Space datetime",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date="2027-06-15 14:30:00",
        )

        assert goal.target_date.year == 2027

    def test_parse_datetime_with_microseconds(self):
        """Parse datetime with microseconds."""
        goal = GoalCreate(
            title="Micro datetime",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date="2027-06-15T14:30:00.123456",
        )

        assert goal.target_date.year == 2027

    def test_parse_python_date_object(self):
        """Accept Python date object."""
        goal = GoalCreate(
            title="Date object",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date=date(2027, 6, 15),
        )

        assert goal.target_date.year == 2027

    def test_parse_python_datetime_object(self):
        """Accept Python datetime object."""
        dt = datetime(2027, 6, 15, 10, 30)
        goal = GoalCreate(
            title="Datetime object",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date=dt,
        )

        assert goal.target_date == dt

    def test_none_target_date(self):
        """Accept None for target_date."""
        goal = GoalCreate(
            title="No date",
            goal_type=GoalType.SAVINGS,
            target_amount=1000,
            target_date=None,
        )

        assert goal.target_date is None


class TestGoalUpdateValidation:
    """Tests for GoalUpdate schema validation."""

    def test_empty_update(self):
        """Accept update with no fields set."""
        update = GoalUpdate()

        assert update.title is None
        assert update.target_amount is None

    def test_partial_update(self):
        """Accept partial update."""
        update = GoalUpdate(title="New title")

        assert update.title == "New title"
        assert update.target_amount is None

    def test_reject_empty_title(self):
        """Reject empty title string."""
        with pytest.raises(ValidationError):
            GoalUpdate(title="")

    def test_reject_negative_target_amount(self):
        """Reject negative target amount."""
        with pytest.raises(ValidationError):
            GoalUpdate(target_amount=-100)

    def test_update_status(self):
        """Accept status update."""
        update = GoalUpdate(status=GoalStatus.PAUSED)

        assert update.status == GoalStatus.PAUSED

    def test_target_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        update = GoalUpdate(target_amount=1000.559)

        assert update.target_amount == 1000.56

    def test_none_target_amount_stays_none(self):
        """None target amount stays None."""
        update = GoalUpdate(target_amount=None)

        assert update.target_amount is None

    def test_date_parsing_works(self):
        """Target date parsing works in update schema."""
        update = GoalUpdate(target_date="2027-06-15")

        assert update.target_date == datetime(2027, 6, 15, 0, 0, 0)


class TestGoalProgressUpdateValidation:
    """Tests for GoalProgressUpdate schema validation."""

    def test_valid_amount(self):
        """Accept valid current amount."""
        progress = GoalProgressUpdate(current_amount=1500.00)

        assert progress.current_amount == 1500.00

    def test_zero_amount(self):
        """Accept zero current amount."""
        progress = GoalProgressUpdate(current_amount=0.0)

        assert progress.current_amount == 0.0

    def test_reject_negative_amount(self):
        """Reject negative current amount."""
        with pytest.raises(ValidationError):
            GoalProgressUpdate(current_amount=-100)

    def test_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        progress = GoalProgressUpdate(current_amount=1500.999)

        assert progress.current_amount == 1501.00

    def test_reject_missing_amount(self):
        """Reject missing current_amount."""
        with pytest.raises(ValidationError):
            GoalProgressUpdate()


class TestMilestoneCreateValidation:
    """Tests for MilestoneCreate schema validation."""

    def test_valid_minimal(self):
        """Accept minimal valid input."""
        milestone = MilestoneCreate(
            title="Milestone 1",
            target_amount=1000.00,
        )

        assert milestone.title == "Milestone 1"
        assert milestone.target_amount == 1000.00
        assert milestone.order_index == 0

    def test_valid_all_fields(self):
        """Accept all fields populated."""
        milestone = MilestoneCreate(
            title="Full milestone",
            description="Detailed description",
            target_amount=2500.00,
            order_index=3,
        )

        assert milestone.description == "Detailed description"
        assert milestone.order_index == 3

    def test_reject_empty_title(self):
        """Reject empty title."""
        with pytest.raises(ValidationError):
            MilestoneCreate(title="", target_amount=1000)

    def test_reject_title_too_long(self):
        """Reject title exceeding 255 characters."""
        with pytest.raises(ValidationError):
            MilestoneCreate(title="x" * 256, target_amount=1000)

    def test_reject_zero_target_amount(self):
        """Reject zero target amount."""
        with pytest.raises(ValidationError):
            MilestoneCreate(title="Zero", target_amount=0)

    def test_reject_negative_target_amount(self):
        """Reject negative target amount."""
        with pytest.raises(ValidationError):
            MilestoneCreate(title="Negative", target_amount=-100)

    def test_target_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        milestone = MilestoneCreate(
            title="Rounded",
            target_amount=999.999,
        )

        assert milestone.target_amount == 1000.00

    def test_description_max_length(self):
        """Reject description exceeding 500 characters."""
        with pytest.raises(ValidationError):
            MilestoneCreate(
                title="Long desc",
                target_amount=1000,
                description="x" * 501,
            )


class TestMilestoneProgressUpdateValidation:
    """Tests for MilestoneProgressUpdate schema validation."""

    def test_valid_amount(self):
        """Accept valid current amount."""
        progress = MilestoneProgressUpdate(current_amount=500.00)

        assert progress.current_amount == 500.00

    def test_zero_amount(self):
        """Accept zero current amount."""
        progress = MilestoneProgressUpdate(current_amount=0.0)

        assert progress.current_amount == 0.0

    def test_reject_negative_amount(self):
        """Reject negative current amount."""
        with pytest.raises(ValidationError):
            MilestoneProgressUpdate(current_amount=-50)

    def test_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        progress = MilestoneProgressUpdate(current_amount=500.999)

        assert progress.current_amount == 501.00


class TestMilestoneUpdateValidation:
    """Tests for MilestoneUpdate schema validation."""

    def test_empty_update(self):
        """Accept update with no fields set."""
        update = MilestoneUpdate()

        assert update.title is None

    def test_reject_negative_target(self):
        """Reject negative target amount."""
        with pytest.raises(ValidationError):
            MilestoneUpdate(target_amount=-100)

    def test_none_target_stays_none(self):
        """None target amount stays None."""
        update = MilestoneUpdate(target_amount=None)

        assert update.target_amount is None

    def test_amount_rounded(self):
        """Amount is rounded to 2 decimal places."""
        update = MilestoneUpdate(target_amount=999.999)

        assert update.target_amount == 1000.00
