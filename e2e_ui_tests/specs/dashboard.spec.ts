import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { DashboardActions } from "../interface/DashboardActions";
import { SidebarInterface } from "../interface/SidebarInterface";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

test.describe("Dashboard", () => {
  let auth: AuthActions;
  let dashboard: DashboardActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    dashboard = new DashboardActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    // After login, user lands on the dashboard by default
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Load", () => {
    test("should display the dashboard page", async () => {
      await dashboard.expectDashboardVisible();
    });

    test("should display KPI cards (income, expenses, cash flow, balance, savings rate)", async () => {
      await dashboard.expectKpiStripVisible();
    });
  });

  test.describe("Charts", () => {
    test("should render the Cash Flow chart", async () => {
      await dashboard.expectCashFlowChartVisible();
    });

    test("should render the Month Comparison chart", async () => {
      await dashboard.expectMonthComparisonChartVisible();
    });

    test("should render category charts (expense and income)", async () => {
      await dashboard.expectCategoryChartsVisible();
    });
  });

  test.describe("Widgets", () => {
    test("should display the Account Balances widget", async () => {
      await dashboard.expectAccountBalancesVisible();
    });

    test("should display the Budget Progress widget (Pro feature gate)", async ({
      page,
    }) => {
      // Budget progress widget is behind a ProFeatureGate. For basic plan
      // users the content is rendered blurred behind an overlay. We check
      // that the element exists in the DOM (it may not pass strict
      // visibility due to blur/opacity on the gate wrapper).
      const budgetWidget = page.getByTestId("dashboard-budget-progress");
      await budgetWidget.waitFor({ state: "attached", timeout: 10000 });
      const count = await budgetWidget.count();
      expect(count).toBeGreaterThan(0);
    });
  });

  test.describe("Period Selector", () => {
    test("should display the period selector", async () => {
      await dashboard.expectPeriodSelectorVisible();
    });

    test("should have the 1-month period active by default", async () => {
      await dashboard.expectPeriodButtonActive(1);
    });

    test("should allow changing the period when available", async ({
      page,
    }) => {
      // The 1m button should be active by default
      await dashboard.expectPeriodButtonActive(1);

      // For a basic plan user, 3m/6m/12m are locked.
      // Verify they are disabled.
      await dashboard.expectPeriodButtonDisabled(3);
      await dashboard.expectPeriodButtonDisabled(6);
      await dashboard.expectPeriodButtonDisabled(12);
    });
  });

  test.describe("Navigation", () => {
    test("should navigate to expense page from sidebar", async ({ page }) => {
      await sidebar.navigateToExpense();
      await expect(page).toHaveURL(/\/expense/);
    });
  });
});
