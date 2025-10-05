import { Page } from '@playwright/test';
import { ExpensePage } from '../infra/pages';
import { CreateExpenseModal } from '../infra/modals';

export interface ExpenseData {
  amount: string | number;
  description: string;
  category: string;
  date?: string;
  account?: string;
  tags?: string[];
}

export class ExpenseActions {
  private page: Page;
  private expensePage: ExpensePage;
  private createExpenseModal: CreateExpenseModal;

  constructor(page: Page) {
    this.page = page;
    this.expensePage = new ExpensePage(page);
    this.createExpenseModal = new CreateExpenseModal(page);
  }

  /**
   * Navigate to expense page
   */
  async goto(): Promise<void> {
    await this.expensePage.goto();
  }

  /**
   * Create a new expense
   */
  async create(expenseData: ExpenseData): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.openCreateModal();
    await this.createExpenseModal.createExpense(expenseData);
    await this.createExpenseModal.waitForModalClose();
  }

  /**
   * Edit existing expense
   */
  async edit(expenseDescription: string, updatedData: Partial<ExpenseData>): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.editExpense(expenseDescription);
    
    // Fill updated data in edit modal
    if (updatedData.amount) {
      await this.createExpenseModal.fillAmount(updatedData.amount);
    }
    if (updatedData.description) {
      await this.createExpenseModal.fillDescription(updatedData.description);
    }
    if (updatedData.category) {
      await this.createExpenseModal.selectCategory(updatedData.category);
    }
    if (updatedData.date) {
      await this.createExpenseModal.fillDate(updatedData.date);
    }
    if (updatedData.account) {
      await this.createExpenseModal.selectAccount(updatedData.account);
    }
    if (updatedData.tags) {
      await this.createExpenseModal.fillTags(updatedData.tags);
    }
    
    await this.createExpenseModal.save();
    await this.createExpenseModal.waitForModalClose();
  }

  /**
   * Delete expense
   */
  async delete(expenseDescription: string): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.deleteExpense(expenseDescription);
    await this.expensePage.confirmDelete();
  }

  /**
   * Search for expenses
   */
  async search(query: string): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.searchExpenses(query);
  }

  /**
   * Filter expenses by category
   */
  async filterByCategory(category: string): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.filterByCategory(category);
  }

  /**
   * Filter expenses by date range
   */
  async filterByDateRange(startDate: string, endDate: string): Promise<void> {
    await this.expensePage.goto();
    await this.expensePage.filterByDateRange(startDate, endDate);
  }

  /**
   * Clear filters
   */
  async clearFilters(): Promise<void> {
    await this.expensePage.clearFilters();
  }

  /**
   * Open create expense modal
   */
  async openCreateModal(): Promise<void> {
    await this.expensePage.openCreateModal();
  }

  /**
   * Fill expense form
   */
  async fillForm(data: ExpenseData): Promise<void> {
    await this.createExpenseModal.fillForm(data);
  }

  /**
   * Save expense
   */
  async save(): Promise<void> {
    await this.createExpenseModal.save();
  }

  /**
   * Cancel expense creation
   */
  async cancel(): Promise<void> {
    await this.createExpenseModal.cancel();
  }

  /**
   * Close expense modal
   */
  async closeModal(): Promise<void> {
    await this.createExpenseModal.close();
  }

  /**
   * Switch to table view
   */
  async switchToTableView(): Promise<void> {
    await this.expensePage.switchToTableView();
  }

  /**
   * Switch to dashboard view
   */
  async switchToDashboardView(): Promise<void> {
    await this.expensePage.switchToDashboardView();
  }

  /**
   * Get expense by description
   */
  getExpenseByDescription(description: string) {
    return this.expensePage.getExpenseByDescription(description);
  }

  /**
   * Check if expense exists
   */
  async exists(description: string): Promise<boolean> {
    return await this.expensePage.expenseExists(description);
  }

  /**
   * Get all visible expenses
   */
  async getAll(): Promise<Array<{ description: string; amount: number; category: string }>> {
    return await this.expensePage.getVisibleExpenses();
  }

  /**
   * Get total expense amount
   */
  async getTotalAmount(): Promise<number> {
    return await this.expensePage.getTotalAmount();
  }

  /**
   * Get expense count
   */
  async getCount(): Promise<number> {
    return await this.expensePage.getExpenseCount();
  }

  /**
   * Sort expenses by column
   */
  async sortBy(column: 'amount' | 'date' | 'category' | 'description'): Promise<void> {
    await this.expensePage.sortBy(column);
  }

  /**
   * Export expenses
   */
  async export(format: 'csv' | 'pdf'): Promise<void> {
    await this.expensePage.exportExpenses(format);
  }

  /**
   * Wait for expense list to load
   */
  async waitForList(): Promise<void> {
    await this.expensePage.waitForExpenseList();
  }

  /**
   * Get validation errors from create modal
   */
  async getValidationErrors(): Promise<string[]> {
    return await this.createExpenseModal.getValidationErrors();
  }

  /**
   * Check if form is valid
   */
  async isFormValid(): Promise<boolean> {
    return await this.createExpenseModal.isFormValid();
  }

  /**
   * Clear form
   */
  async clearForm(): Promise<void> {
    await this.createExpenseModal.clearForm();
  }

  /**
   * Get available categories
   */
  async getAvailableCategories(): Promise<string[]> {
    return await this.createExpenseModal.getAvailableCategories();
  }

  /**
   * Get available accounts
   */
  async getAvailableAccounts(): Promise<string[]> {
    return await this.createExpenseModal.getAvailableAccounts();
  }
}

