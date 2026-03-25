import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { GoalsActions, GoalData } from "../interface/GoalsActions";
import { SidebarInterface } from "../interface/SidebarInterface";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

const generateGoalData = (): GoalData => {
  const timestamp = Date.now();
  return {
    title: `Test Goal ${timestamp}`,
    description: `Test goal description ${timestamp}`,
    goalType: "SAVINGS",
    priority: "MEDIUM",
    targetAmount: "10000",
  };
};

test.describe("Goals Management", () => {
  let auth: AuthActions;
  let goals: GoalsActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    goals = new GoalsActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToGoals();
  });

  test.describe("View Goals", () => {
    test("should display goals page with header and summary strip", async () => {
      await goals.expectPageVisible();
      await goals.expectSummaryStripVisible();
    });

    test("should display goal table", async () => {
      await goals.expectGoalTableVisible();
    });
  });

  test.describe("Create Goal", () => {
    test("should create a savings goal", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);
    });
  });

  test.describe("Update Goal Progress", () => {
    test("should update goal progress amount", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);

      await goals.updateGoalProgress(goalData.title, "5000");
      // After updating progress, goal should still be visible
      await goals.expectGoalVisible(goalData.title);
      // Progress should show 50% (5000/10000)
      await goals.expectGoalProgressPercentage(goalData.title, "50.0%");
    });
  });

  test.describe("Edit Goal", () => {
    test("should edit goal details", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);

      const updatedTitle = `Updated Goal ${Date.now()}`;
      await goals.editGoal(goalData.title, { title: updatedTitle });
      await goals.expectGoalVisible(updatedTitle);
    });
  });

  test.describe("Goal Statistics", () => {
    test("should show goal statistics in summary strip after creating a goal", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);
      await goals.expectSummaryStripVisible();
    });
  });

  test.describe("Mark Goal as Completed", () => {
    test("should mark goal as completed by updating progress to target", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);

      // Update progress to target amount to complete the goal
      await goals.updateGoalProgress(goalData.title, "10000");
      await goals.expectGoalVisible(goalData.title);
      await goals.expectGoalProgressPercentage(goalData.title, "100.0%");
    });
  });

  test.describe("Delete Goal", () => {
    test("should delete a goal", async () => {
      const goalData = generateGoalData();
      await goals.createGoal(goalData);
      await goals.expectGoalVisible(goalData.title);

      await goals.deleteGoal(goalData.title);
      await goals.expectGoalHidden(goalData.title);
    });
  });
});
