"""E2E tests for goals CRUD, milestones, and progress tracking."""
import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.goals


class TestGoalCRUD:

    async def _create_test_goal(self, goals_client, **overrides):
        payload = {
            "title": "E2E Test Goal",
            "goal_type": "SAVINGS",
            "target_amount": 10000.00,
            "currency": "USD",
            "priority": "MEDIUM",
            **overrides,
        }
        return (await goals_client.create_goal(**payload)).raise_on_error()

    async def test_create_goal(self, goals_client):
        data = await self._create_test_goal(goals_client, title="Save for vacation")
        assert data["title"] == "Save for vacation"
        assert data["goal_type"] == "SAVINGS"
        assert data["target_amount"] == 10000.00
        assert data["current_amount"] == 0.0
        assert data["status"] == "ACTIVE"
        assert "id" in data

    async def test_create_goal_all_types(self, goals_client):
        for goal_type in ["SAVINGS", "DEBT_PAYOFF", "INVESTMENT", "EMERGENCY_FUND"]:
            data = await self._create_test_goal(
                goals_client, title=f"Goal {goal_type}", goal_type=goal_type
            )
            assert data["goal_type"] == goal_type

    async def test_create_goal_with_target_date(self, goals_client):
        target = (date.today() + timedelta(days=365)).isoformat()
        data = await self._create_test_goal(
            goals_client, title="Deadline Goal", target_date=target
        )
        assert data["target_date"] is not None

    async def test_list_goals(self, goals_client):
        await self._create_test_goal(goals_client, title="Listed Goal")
        result = await goals_client.list_goals()
        data = result.raise_on_error()
        assert "items" in data
        assert data["total"] >= 1

    async def test_get_goal(self, goals_client):
        created = await self._create_test_goal(goals_client, title="Fetch Goal")
        result = await goals_client.get_goal(created["id"])
        data = result.raise_on_error()
        assert data["id"] == created["id"]
        assert data["title"] == "Fetch Goal"

    async def test_update_goal(self, goals_client):
        created = await self._create_test_goal(goals_client, title="Before Update")
        result = await goals_client.update_goal(
            created["id"], title="After Update", priority="HIGH"
        )
        data = result.raise_on_error()
        assert data["title"] == "After Update"
        assert data["priority"] == "HIGH"

    async def test_delete_goal(self, goals_client):
        created = await self._create_test_goal(goals_client, title="Delete Goal")
        result = await goals_client.delete_goal(created["id"])
        assert result.status_code == 204

    async def test_get_nonexistent_goal(self, goals_client):
        result = await goals_client.get_goal(999999)
        assert not result.ok

    async def test_create_goal_invalid_amount(self, goals_client):
        result = await goals_client.create_goal(
            title="Bad Goal",
            goal_type="SAVINGS",
            target_amount=-100.0,
            currency="USD",
        )
        assert not result.ok


class TestGoalProgress:

    async def test_update_progress(self, goals_client):
        goal = (await goals_client.create_goal(
            title="Progress Goal",
            goal_type="SAVINGS",
            target_amount=1000.00,
            currency="USD",
        )).raise_on_error()

        result = await goals_client.update_progress(goal["id"], current_amount=500.0)
        data = result.raise_on_error()
        assert data["current_amount"] == 500.0
        assert data["progress_percentage"] == 50.0

    async def test_goal_auto_completes(self, goals_client):
        goal = (await goals_client.create_goal(
            title="Complete Goal",
            goal_type="SAVINGS",
            target_amount=100.00,
            currency="USD",
        )).raise_on_error()

        result = await goals_client.update_progress(goal["id"], current_amount=100.0)
        data = result.raise_on_error()
        assert data["progress_percentage"] == 100.0
        assert data["status"] == "COMPLETED"


class TestMilestones:

    async def _create_goal_with_milestones_enabled(self, goals_client):
        return (await goals_client.create_goal(
            title="Milestone Goal",
            goal_type="SAVINGS",
            target_amount=10000.00,
            currency="USD",
            is_milestone_based=True,
        )).raise_on_error()

    async def test_create_milestone(self, goals_client):
        goal = await self._create_goal_with_milestones_enabled(goals_client)
        result = await goals_client.create_milestone(
            goal["id"],
            title="First milestone",
            target_amount=2500.00,
            order_index=0,
        )
        data = result.raise_on_error()
        assert data["title"] == "First milestone"
        assert data["target_amount"] == 2500.00
        assert data["is_completed"] is False

    async def test_list_milestones(self, goals_client):
        goal = await self._create_goal_with_milestones_enabled(goals_client)
        await goals_client.create_milestone(
            goal["id"], title="MS 1", target_amount=1000.00, order_index=0
        )
        await goals_client.create_milestone(
            goal["id"], title="MS 2", target_amount=2000.00, order_index=1
        )
        result = await goals_client.list_milestones(goal["id"])
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_update_milestone_progress(self, goals_client):
        goal = await self._create_goal_with_milestones_enabled(goals_client)
        ms = (await goals_client.create_milestone(
            goal["id"], title="Track MS", target_amount=500.00, order_index=0
        )).raise_on_error()

        result = await goals_client.update_milestone_progress(
            goal["id"], ms["id"], current_amount=500.0
        )
        data = result.raise_on_error()
        assert data["current_amount"] == 500.0
        assert data["is_completed"] is True


class TestGoalStatistics:

    async def test_get_statistics(self, goals_client):
        # Create a goal so stats are meaningful
        await goals_client.create_goal(
            title="Stats Goal",
            goal_type="SAVINGS",
            target_amount=5000.00,
            currency="USD",
        )
        result = await goals_client.get_statistics()
        data = result.raise_on_error()
        assert "total_goals" in data
        assert "active_goals" in data
        assert "overall_progress" in data
        assert data["total_goals"] >= 1
