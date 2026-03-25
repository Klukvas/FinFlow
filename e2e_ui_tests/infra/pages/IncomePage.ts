import { Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class IncomePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page header
  get pageTitle() {
    return this.page.locator("h1");
  }

  // Add income button (last primary button in header area)
  get addIncomeButton() {
    return this.page
      .locator('button:has(svg path[d="M12 4v16m8-8H4"])')
      .first();
  }

  // Filter toggle button
  get filterToggleButton() {
    return this.page
      .locator('button:has(svg path[d*="M3 4a1 1 0 011-1h16"])')
      .first();
  }

  // Summary strip (KPI cards)
  get summaryStrip() {
    return this.page.locator(".grid.grid-cols-2");
  }

  get summaryCards() {
    return this.summaryStrip
      .locator('[class*="Card"]')
      .or(this.summaryStrip.locator(".bg-elevated, .rounded-xl"));
  }

  // Table
  get table() {
    return this.page.locator("table").first();
  }

  get tableRows() {
    return this.table.locator("tbody tr");
  }

  // Filter bar
  get filterBar() {
    return this.page.locator(".bg-elevated.border.rounded-xl.p-4");
  }

  get filterCategorySelect() {
    return this.filterBar.locator("select").nth(0);
  }

  // Modal
  get modal() {
    return this.page.locator('[data-testid="modal"]');
  }

  get modalCloseButton() {
    return this.page.getByTestId("modal-close-button");
  }

  // Delete confirmation button - the danger/red button in the confirm modal
  get deleteConfirmButton() {
    // The confirm button is always the last button in the modal's footer row
    return this.modal.locator(".flex.justify-end.gap-3 button").last();
  }

  // Income row actions
  getIncomeRowByAmount(amount: string) {
    return this.table.locator("tbody tr").filter({
      hasText: amount,
    });
  }

  getDeleteButtonInRow(row: ReturnType<typeof this.getIncomeRowByAmount>) {
    return row.locator('button:has(svg path[d*="M19 7l-.867 12.142"])');
  }

  // Pagination
  get pagination() {
    return this.page.locator(
      '[class*="pagination"], nav[aria-label*="pagination"]',
    );
  }

  async expectPageVisible(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectTableVisible(): Promise<void> {
    await expect(this.table).toBeVisible();
  }

  async expectEmptyState(): Promise<void> {
    const emptyMessage = this.page.locator("text=/no.*income|нет.*доходов/i");
    await expect(emptyMessage).toBeVisible();
  }
}
