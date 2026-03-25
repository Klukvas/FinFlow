import { expect, Page } from "@playwright/test";
import { RecurringPage } from "../infra/pages/RecurringPage";
import { RecurringModal, RecurringFormData } from "../infra/modals/RecurringModal";
import { DeleteConfirmModal } from "../infra/modals/DeleteConfirmModal";

export class RecurringActions {
  private page: Page;
  private recurringPage: RecurringPage;
  private recurringModal: RecurringModal;
  private deleteModal: DeleteConfirmModal;

  constructor(page: Page) {
    this.page = page;
    this.recurringPage = new RecurringPage(page);
    this.recurringModal = new RecurringModal(page);
    this.deleteModal = new DeleteConfirmModal(page);
  }

  // --- Create ---

  async openCreateModal(): Promise<void> {
    await this.recurringPage.addButton.click();
    await this.recurringModal.expectModal();
  }

  async createRecurringPayment(data: RecurringFormData): Promise<void> {
    await this.openCreateModal();
    await this.recurringModal.fillForm(data);
    await this.recurringModal.submitAndExpectClosed();
    // Wait for data to refresh
    await this.page.waitForTimeout(2000);
  }

  // --- List ---

  async expectPaymentVisible(name: string): Promise<void> {
    await expect(
      this.recurringPage.getPaymentRowByName(name),
    ).toBeVisible({ timeout: 10000 });
  }

  async expectPaymentHidden(name: string): Promise<void> {
    await expect(
      this.recurringPage.getPaymentRowByName(name),
    ).toBeHidden({ timeout: 10000 });
  }

  async expectTableVisible(): Promise<void> {
    await expect(this.recurringPage.table).toBeVisible({ timeout: 10000 });
  }

  // --- Side Panel ---

  async openSidePanel(name: string): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    await row.click();
    await expect(this.recurringPage.sidePanel).toBeVisible({ timeout: 5000 });
    await this.page.waitForTimeout(500);
  }

  async closeSidePanel(): Promise<void> {
    await this.page.keyboard.press("Escape");
    await this.page.waitForTimeout(500);
  }

  // --- Upcoming Executions ---

  async expectUpcomingExecutionsVisible(): Promise<void> {
    const upcomingTitle = this.page.locator("h3").filter({ hasText: /upcoming/i }).first();
    await expect(upcomingTitle).toBeVisible({ timeout: 10000 });
  }

  // --- Pause/Resume ---

  async pausePaymentFromTable(name: string): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    // The pause button is the first button in actions (for active payments)
    const pauseButton = row.locator("td:last-child button").first();
    await pauseButton.click();
    // Wait for status update
    await this.page.waitForTimeout(2000);
  }

  async resumePaymentFromTable(name: string): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    // The resume button is the first button in actions (for paused payments)
    const resumeButton = row.locator("td:last-child button").first();
    await resumeButton.click();
    // Wait for status update
    await this.page.waitForTimeout(2000);
  }

  async pausePaymentFromSidePanel(): Promise<void> {
    const pauseButton = this.recurringPage.sidePanel.locator("button").filter({ hasText: /pause/i }).first();
    await pauseButton.click();
    await this.page.waitForTimeout(2000);
  }

  async resumePaymentFromSidePanel(): Promise<void> {
    const resumeButton = this.recurringPage.sidePanel.locator("button").filter({ hasText: /resume/i }).first();
    await resumeButton.click();
    await this.page.waitForTimeout(2000);
  }

  async expectPaymentStatus(name: string, status: string): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    // Status is shown in a Badge component in the status column
    const statusBadge = row.locator("span").filter({ hasText: new RegExp(status, "i") }).first();
    await expect(statusBadge).toBeVisible({ timeout: 10000 });
  }

  // --- Edit ---

  async editPaymentFromTable(name: string, updatedData: Partial<RecurringFormData>): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    // Edit button is second-to-last in the actions cell
    const editButton = row.locator("td:last-child button").nth(-2);
    await editButton.click();
    await this.recurringModal.expectModal();

    if (updatedData.name !== undefined) {
      await this.recurringModal.nameInput.clear();
      await this.recurringModal.nameInput.fill(updatedData.name);
    }
    if (updatedData.description !== undefined) {
      await this.recurringModal.descriptionInput.clear();
      await this.recurringModal.descriptionInput.fill(updatedData.description);
    }
    if (updatedData.amount !== undefined) {
      await this.recurringModal.amountInput.clear();
      await this.recurringModal.amountInput.fill(updatedData.amount);
    }

    await this.recurringModal.submitAndExpectClosed();
    await this.page.waitForTimeout(2000);
  }

  async editPaymentFromSidePanel(updatedData: Partial<RecurringFormData>): Promise<void> {
    const editButton = this.recurringPage.sidePanel.locator("button").filter({ hasText: /^edit$/i }).first();
    await editButton.click();
    await this.recurringModal.expectModal();

    if (updatedData.name !== undefined) {
      await this.recurringModal.nameInput.clear();
      await this.recurringModal.nameInput.fill(updatedData.name);
    }
    if (updatedData.description !== undefined) {
      await this.recurringModal.descriptionInput.clear();
      await this.recurringModal.descriptionInput.fill(updatedData.description);
    }
    if (updatedData.amount !== undefined) {
      await this.recurringModal.amountInput.clear();
      await this.recurringModal.amountInput.fill(updatedData.amount);
    }

    await this.recurringModal.submitAndExpectClosed();
    await this.page.waitForTimeout(2000);
  }

  // --- Delete ---

  async deletePaymentFromTable(name: string): Promise<void> {
    const row = this.recurringPage.getPaymentRowByName(name);
    // Delete button is the last button in the actions cell
    const deleteButton = row.locator("td:last-child button").last();
    await deleteButton.click();
    await this.deleteModal.expectModal();
    await this.deleteModal.confirm();
    await this.page.waitForTimeout(1000);
  }

  async deletePaymentFromSidePanel(): Promise<void> {
    const deleteButton = this.recurringPage.sidePanel.locator("button").filter({ hasText: /delete/i }).first();
    await deleteButton.click();
    await this.deleteModal.expectModal();
    await this.deleteModal.confirm();
    await this.page.waitForTimeout(1000);
  }

  // --- Statistics ---

  async expectSummaryStripVisible(): Promise<void> {
    const kpiCards = this.page.locator(".grid > div").filter({ hasText: /total|active|paused|expense|income/i });
    await expect(kpiCards.first()).toBeVisible({ timeout: 10000 });
  }
}
