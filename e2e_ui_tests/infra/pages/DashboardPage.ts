import { Page } from "@playwright/test";
import { BasePage } from "../BasePage";

export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page container
  get dashboardPage() {
    return this.getByTestId("dashboard-page");
  }

  // KPI Strip
  get kpiStrip() {
    return this.getByTestId("dashboard-kpi-strip");
  }

  get kpiIncome() {
    return this.getByTestId("dashboard-kpi-income");
  }

  get kpiExpenses() {
    return this.getByTestId("dashboard-kpi-expenses");
  }

  get kpiCashFlow() {
    return this.getByTestId("dashboard-kpi-cashFlow");
  }

  get kpiBalance() {
    return this.getByTestId("dashboard-kpi-balance");
  }

  get kpiSavingsRate() {
    return this.getByTestId("dashboard-kpi-savingsRate");
  }

  // Charts
  get cashFlowChart() {
    return this.getByTestId("dashboard-cash-flow-chart");
  }

  get monthComparisonChart() {
    return this.getByTestId("dashboard-month-comparison-chart");
  }

  get expenseCategoryChart() {
    return this.getByTestId("dashboard-expense-category-chart");
  }

  get incomeCategoryChart() {
    return this.getByTestId("dashboard-income-category-chart");
  }

  // Widgets
  get accountBalances() {
    return this.getByTestId("dashboard-account-balances");
  }

  get budgetProgress() {
    return this.getByTestId("dashboard-budget-progress");
  }

  // Period selector
  get periodSelector() {
    return this.getByTestId("dashboard-period-selector");
  }

  getPeriodButton(months: number) {
    return this.getByTestId(`period-${months}m`);
  }
}
