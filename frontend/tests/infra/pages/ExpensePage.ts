import { Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class ExpensePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Element selectors using data-testid
  get createExpenseButton() { return this.getByTestId('create-expense-button'); }
  get expenseList() { return this.getByTestId('expense-list'); }
  get expenseDashboard() { return this.getByTestId('expense-dashboard'); }
  get searchInput() { return this.getByTestId('expense-search'); }
  get filterButton() { return this.getByTestId('expense-filter-button'); }
  get tableTab() { return this.getByTestId('expense-table-tab'); }
  get dashboardTab() { return this.getByTestId('expense-dashboard-tab'); }
  get pageHeader() { return this.getByTestId('expense-page-header'); }
  get totalExpenses() { return this.getByTestId('total-expenses'); }
  get expenseCount() { return this.getByTestId('expense-count'); }

  // Helper method to get expense item selector
  getExpenseItem(expenseId: string) {
    return this.getByTestId(`expense-item-${expenseId}`);
  }

  // Element expectations using expect
  async expectExpenseVisible(expenseId: string): Promise<void> {
    await expect(this.getExpenseItem(expenseId)).toBeVisible();
  }

  async expectExpenseHidden(expenseId: string): Promise<void> {
    await expect(this.getExpenseItem(expenseId)).toBeHidden();
  }

  async expectExpenseListVisible(): Promise<void> {
    await expect(this.expenseList).toBeVisible();
  }

  async expectDashboardVisible(): Promise<void> {
    await expect(this.expenseDashboard).toBeVisible();
  }

  async expectTotalExpensesVisible(): Promise<void> {
    await expect(this.totalExpenses).toBeVisible();
  }

  async expectExpenseCountVisible(): Promise<void> {
    await expect(this.expenseCount).toBeVisible();
  }
}