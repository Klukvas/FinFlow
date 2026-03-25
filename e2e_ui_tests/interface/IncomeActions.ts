import { expect, Page } from "@playwright/test";
import { IncomePage } from "../infra/pages/IncomePage";
import { CreateIncomeModal } from "../infra/modals/CreateIncomeModal";

export interface IncomeFormData {
  amount: string;
  description?: string;
  date?: string;
  categoryName?: string;
  accountName?: string;
}

export class IncomeActions {
  private page: Page;
  private incomePage: IncomePage;
  private incomeModal: CreateIncomeModal;

  constructor(page: Page) {
    this.page = page;
    this.incomePage = new IncomePage(page);
    this.incomeModal = new CreateIncomeModal(page);
  }

  // --- Create ---

  async createIncome(data: IncomeFormData): Promise<void> {
    await this.openCreateModal();
    await this.incomeModal.fillForm(data);
    await this.incomeModal.submit();
    await this.incomeModal.waitForModalClose();
    await this.page.waitForLoadState("networkidle");
  }

  async openCreateModal(): Promise<void> {
    await this.incomePage.addIncomeButton.click();
    await this.incomeModal.expectModalVisible();
  }

  // --- Delete ---

  async deleteIncome(identifyingText: string): Promise<void> {
    const row = this.incomePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row.first()).toBeVisible();
    const deleteButton = this.incomePage.getDeleteButtonInRow(row.first());
    await deleteButton.click();

    // Confirm deletion
    const confirmModal = this.incomePage.modal;
    await expect(confirmModal).toBeVisible();
    await this.incomePage.deleteConfirmButton.click();
    await expect(confirmModal).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
  }

  // --- Assertions ---

  async expectIncomeVisible(identifyingText: string): Promise<void> {
    const row = this.incomePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row.first()).toBeVisible({ timeout: 10000 });
  }

  async expectIncomeNotVisible(identifyingText: string): Promise<void> {
    // The table might not exist if list is empty (empty state renders instead)
    const tableVisible = await this.incomePage.table
      .isVisible()
      .catch(() => false);
    if (!tableVisible) {
      return; // No table means no incomes, so the item is definitely not visible
    }
    const row = this.incomePage.table
      .locator("tbody tr")
      .filter({ hasText: identifyingText });
    await expect(row).toHaveCount(0, { timeout: 10000 });
  }

  async expectTableVisible(): Promise<void> {
    await this.incomePage.expectTableVisible();
  }

  async expectSummaryStripVisible(): Promise<void> {
    await expect(this.incomePage.summaryStrip).toBeVisible();
  }

  async expectTableRowCount(count: number): Promise<void> {
    await expect(this.incomePage.tableRows).toHaveCount(count);
  }

  // --- Filters ---

  async openFilters(): Promise<void> {
    await this.incomePage.filterToggleButton.click();
    await expect(this.incomePage.filterBar).toBeVisible();
  }

  async filterByCategory(categoryName: string): Promise<void> {
    const categorySelect = this.incomePage.filterBar.locator("select").first();
    await categorySelect.selectOption({ label: categoryName });
    await this.page.waitForLoadState("networkidle");
    // Allow time for client-side filtering
    await this.page.waitForTimeout(500);
  }

  async clearFilters(): Promise<void> {
    const clearButton = this.incomePage.filterBar.locator("button").last();
    await clearButton.click();
    await this.page.waitForLoadState("networkidle");
  }

  // --- Pagination ---

  async expectPaginationVisible(): Promise<void> {
    await expect(this.incomePage.pagination.first()).toBeVisible();
  }
}
