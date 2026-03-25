import { expect, Page } from "@playwright/test";
import { ExpensePage } from "../infra/pages/ExpensePage";
import { CreateExpenseModal } from "../infra/modals/CreateExpenseModal";

export interface ExpenseFormData {
  amount: string;
  description?: string;
  date?: string;
  categoryName?: string;
  accountName?: string;
}

export class ExpenseActions {
  private page: Page;
  private expensePage: ExpensePage;
  private expenseModal: CreateExpenseModal;

  constructor(page: Page) {
    this.page = page;
    this.expensePage = new ExpensePage(page);
    this.expenseModal = new CreateExpenseModal(page);
  }

  // --- Create ---

  async createExpense(data: ExpenseFormData): Promise<void> {
    await this.openCreateModal();
    await this.expenseModal.fillForm(data);
    await this.expenseModal.submit();
    await this.expenseModal.waitForModalClose();
    await this.page.waitForLoadState("networkidle");
  }

  async openCreateModal(): Promise<void> {
    await this.expensePage.addExpenseButton.click();
    await this.expenseModal.expectModalVisible();
  }

  // --- Edit ---

  async editExpense(
    identifyingText: string,
    updatedData: Partial<ExpenseFormData>,
  ): Promise<void> {
    await this.openEditModal(identifyingText);
    await this.expenseModal.fillEditForm(updatedData);
    await this.expenseModal.submitEdit();
    await this.expenseModal.waitForModalClose();
    await this.page.waitForLoadState("networkidle");
  }

  async openEditModal(identifyingText: string): Promise<void> {
    const row = this.expensePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row.first()).toBeVisible();
    const editButton = row.first().getByTestId("edit-button");
    await editButton.click();
    await this.expenseModal.expectModalVisible();
    // Wait for edit form to be present
    await expect(this.page.getByTestId("edit-expense-modal")).toBeVisible();
  }

  // --- Delete ---

  async deleteExpense(identifyingText: string): Promise<void> {
    const row = this.expensePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row.first()).toBeVisible();
    const deleteButton = this.expensePage.getDeleteButtonInRow(row.first());
    await deleteButton.click();

    // Confirm deletion
    const confirmModal = this.expensePage.modal;
    await expect(confirmModal).toBeVisible();
    await this.expensePage.deleteConfirmButton.click();
    await expect(confirmModal).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
  }

  // --- Assertions ---

  async expectExpenseVisible(identifyingText: string): Promise<void> {
    const row = this.expensePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row.first()).toBeVisible({ timeout: 10000 });
  }

  async expectExpenseNotVisible(identifyingText: string): Promise<void> {
    // The table might not exist if list is empty (empty state renders instead)
    const tableVisible = await this.expensePage.table
      .isVisible()
      .catch(() => false);
    if (!tableVisible) {
      return; // No table means no expenses, so the item is definitely not visible
    }
    const row = this.expensePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row).toHaveCount(0, { timeout: 10000 });
  }

  async expectTableVisible(): Promise<void> {
    await this.expensePage.expectTableVisible();
  }

  async expectSummaryStripVisible(): Promise<void> {
    await expect(this.expensePage.summaryStrip).toBeVisible();
  }

  async expectTableRowCount(count: number): Promise<void> {
    await expect(this.expensePage.tableRows).toHaveCount(count);
  }

  // --- Filters ---

  async openFilters(): Promise<void> {
    await this.expensePage.filterToggleButton.click();
    await expect(this.expensePage.filterBar).toBeVisible();
  }

  async filterByCategory(categoryName: string): Promise<void> {
    // Filter bar category select is a native <select>
    const categorySelect = this.expensePage.filterBar.locator("select").first();
    await categorySelect.selectOption({ label: categoryName });
    await this.page.waitForLoadState("networkidle");
    // Allow time for client-side filtering
    await this.page.waitForTimeout(500);
  }

  async clearFilters(): Promise<void> {
    // Click "Clear all" button inside filter bar
    const clearButton = this.expensePage.filterBar.locator("button").last();
    await clearButton.click();
    await this.page.waitForLoadState("networkidle");
  }

  // --- Pagination ---

  async expectPaginationVisible(): Promise<void> {
    await expect(this.expensePage.pagination.first()).toBeVisible();
  }
}
