import { expect, Page } from "@playwright/test";
import { DashboardPage } from "../infra/pages/DashboardPage";

export class DashboardActions {
  private dashboardPage: DashboardPage;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.dashboardPage = new DashboardPage(page);
  }

  // Page visibility
  async expectDashboardVisible(): Promise<void> {
    await expect(this.dashboardPage.dashboardPage).toBeVisible();
  }

  // KPI Strip
  async expectKpiStripVisible(): Promise<void> {
    await expect(this.dashboardPage.kpiStrip).toBeVisible();
    await expect(this.dashboardPage.kpiIncome).toBeVisible();
    await expect(this.dashboardPage.kpiExpenses).toBeVisible();
    await expect(this.dashboardPage.kpiCashFlow).toBeVisible();
    await expect(this.dashboardPage.kpiBalance).toBeVisible();
    await expect(this.dashboardPage.kpiSavingsRate).toBeVisible();
  }

  // Cash Flow Chart
  async expectCashFlowChartVisible(): Promise<void> {
    await expect(this.dashboardPage.cashFlowChart).toBeVisible();
  }

  // Month Comparison Chart
  async expectMonthComparisonChartVisible(): Promise<void> {
    await expect(this.dashboardPage.monthComparisonChart).toBeVisible();
  }

  // Category Charts
  async expectExpenseCategoryChartVisible(): Promise<void> {
    await expect(this.dashboardPage.expenseCategoryChart).toBeVisible();
  }

  async expectIncomeCategoryChartVisible(): Promise<void> {
    await expect(this.dashboardPage.incomeCategoryChart).toBeVisible();
  }

  async expectCategoryChartsVisible(): Promise<void> {
    await this.expectExpenseCategoryChartVisible();
    await this.expectIncomeCategoryChartVisible();
  }

  // Account Balances
  async expectAccountBalancesVisible(): Promise<void> {
    await expect(this.dashboardPage.accountBalances).toBeVisible();
  }

  // Budget Progress
  async expectBudgetProgressVisible(): Promise<void> {
    await expect(this.dashboardPage.budgetProgress).toBeVisible();
  }

  // Period Selector
  async expectPeriodSelectorVisible(): Promise<void> {
    await expect(this.dashboardPage.periodSelector).toBeVisible();
  }

  async selectPeriod(months: number): Promise<void> {
    const button = this.dashboardPage.getPeriodButton(months);
    await expect(button).toBeVisible();
    await button.click();
    await this.page.waitForLoadState("networkidle");
  }

  async expectPeriodButtonActive(months: number): Promise<void> {
    const button = this.dashboardPage.getPeriodButton(months);
    await expect(button).toBeVisible();
    // Active button has specific class
    await expect(button).toHaveClass(/bg-accent-base/);
  }

  async expectPeriodButtonDisabled(months: number): Promise<void> {
    const button = this.dashboardPage.getPeriodButton(months);
    await expect(button).toBeDisabled();
  }

  // Navigate to expense from dashboard link
  async navigateToExpenseFromDashboard(): Promise<void> {
    // The dashboard doesn't have a direct expense navigation link in the
    // current markup, but the sidebar does.
    // In tests we use sidebar navigation
  }
}
