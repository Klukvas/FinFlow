import { expect, Page } from "@playwright/test";
import { DebtsPage } from "../infra/pages/DebtsPage";
import { DebtModal, DebtFormData } from "../infra/modals/DebtModal";
import { ContactModal, ContactFormData } from "../infra/modals/ContactModal";
import { PaymentModal, PaymentFormData } from "../infra/modals/PaymentModal";
import { DeleteConfirmModal } from "../infra/modals/DeleteConfirmModal";

export class DebtActions {
  private page: Page;
  private debtsPage: DebtsPage;
  private debtModal: DebtModal;
  private contactModal: ContactModal;
  private paymentModal: PaymentModal;
  private deleteModal: DeleteConfirmModal;

  constructor(page: Page) {
    this.page = page;
    this.debtsPage = new DebtsPage(page);
    this.debtModal = new DebtModal(page);
    this.contactModal = new ContactModal(page);
    this.paymentModal = new PaymentModal(page);
    this.deleteModal = new DeleteConfirmModal(page);
  }

  // --- Contact Actions ---

  async switchToContactsTab(): Promise<void> {
    await this.debtsPage.contactsTab.click();
    await this.page.waitForTimeout(500);
  }

  async switchToDebtsTab(): Promise<void> {
    await this.debtsPage.debtsTab.click();
    await this.page.waitForTimeout(500);
  }

  async createContact(data: ContactFormData): Promise<void> {
    await this.switchToContactsTab();
    // Click the "Add Contact" button - could be in the table empty state or as a header action
    const addContactButton = this.page.locator("button").filter({ hasText: /add.*contact|create.*contact/i }).first();
    await addContactButton.click();
    await this.contactModal.expectModal();
    await this.contactModal.fillForm(data);
    await this.contactModal.submitAndExpectClosed();
    // Wait for the contact to appear
    await this.page.waitForTimeout(1000);
  }

  async expectContactVisible(contactName: string): Promise<void> {
    await this.switchToContactsTab();
    await expect(this.page.locator("td, div").filter({ hasText: contactName }).first()).toBeVisible({ timeout: 10000 });
  }

  // --- Debt Actions ---

  async openCreateDebtModal(): Promise<void> {
    await this.debtsPage.addDebtButton.click();
    await this.debtModal.expectModal();
  }

  async createDebt(data: DebtFormData): Promise<void> {
    await this.openCreateDebtModal();
    await this.debtModal.fillForm(data);
    await this.debtModal.submitAndExpectClosed();
    // Wait for debt to appear in the table
    await this.page.waitForTimeout(1000);
  }

  async expectDebtVisible(debtName: string): Promise<void> {
    await expect(
      this.debtsPage.getDebtRowByName(debtName),
    ).toBeVisible({ timeout: 10000 });
  }

  async expectDebtHidden(debtName: string): Promise<void> {
    await expect(
      this.debtsPage.getDebtRowByName(debtName),
    ).toBeHidden({ timeout: 10000 });
  }

  async openDebtSidePanel(debtName: string): Promise<void> {
    const debtRow = this.debtsPage.getDebtRowByName(debtName);
    await debtRow.click();
    // Wait for side panel to slide in
    await expect(this.debtsPage.sidePanel).toBeVisible({ timeout: 5000 });
    await this.page.waitForTimeout(500);
  }

  async closeSidePanel(): Promise<void> {
    // Press Escape to close
    await this.page.keyboard.press("Escape");
    await this.page.waitForTimeout(500);
  }

  // --- Payment Actions ---

  async makePaymentFromTable(debtName: string, paymentData: PaymentFormData): Promise<void> {
    const debtRow = this.debtsPage.getDebtRowByName(debtName);
    // Click the make-payment button (+ icon) on the row
    const paymentButton = debtRow.locator("td:last-child button").first();
    await paymentButton.click();
    await this.paymentModal.expectModal();
    await this.paymentModal.fillForm(paymentData);
    await this.paymentModal.submitAndExpectClosed();
    await this.page.waitForTimeout(1000);
  }

  async makePaymentFromSidePanel(paymentData: PaymentFormData): Promise<void> {
    // Click "Make Payment" button in the side panel footer
    const makePaymentButton = this.debtsPage.sidePanel.locator("button").filter({ hasText: /make.*payment/i }).first();
    await makePaymentButton.click();
    await this.paymentModal.expectModal();
    await this.paymentModal.fillForm(paymentData);
    await this.paymentModal.submitAndExpectClosed();
    await this.page.waitForTimeout(1000);
  }

  async expectPaymentHistoryInSidePanel(): Promise<void> {
    // The side panel shows "Payment History" section with a table
    const paymentHistoryHeader = this.debtsPage.sidePanel.locator("h3").filter({ hasText: /payment.*history/i });
    await expect(paymentHistoryHeader).toBeVisible({ timeout: 5000 });
  }

  async expectPaymentCountInSidePanel(count: number): Promise<void> {
    // The payment count appears near the payment history header
    const countText = this.debtsPage.sidePanel.locator("span").filter({ hasText: new RegExp(`${count}\\s*payment`, "i") });
    await expect(countText).toBeVisible({ timeout: 5000 });
  }

  // --- Edit Actions ---

  async editDebtFromTable(debtName: string, updatedData: Partial<DebtFormData>): Promise<void> {
    const debtRow = this.debtsPage.getDebtRowByName(debtName);
    // Click the edit button on the row
    const editButton = debtRow.locator("td:last-child button").nth(1);
    await editButton.click();
    await this.debtModal.expectModal();
    if (updatedData.name !== undefined) {
      await this.debtModal.nameInput.clear();
      await this.debtModal.nameInput.fill(updatedData.name);
    }
    if (updatedData.description !== undefined) {
      await this.debtModal.descriptionInput.clear();
      await this.debtModal.descriptionInput.fill(updatedData.description);
    }
    if (updatedData.interestRate !== undefined) {
      await this.debtModal.interestRateInput.clear();
      await this.debtModal.interestRateInput.fill(updatedData.interestRate);
    }
    await this.debtModal.submitAndExpectClosed();
    await this.page.waitForTimeout(1000);
  }

  async editDebtFromSidePanel(updatedData: Partial<DebtFormData>): Promise<void> {
    // Click the "Edit" button in side panel footer
    const editButton = this.debtsPage.sidePanel.locator("button").filter({ hasText: /^edit$/i }).first();
    await editButton.click();
    await this.debtModal.expectModal();
    if (updatedData.name !== undefined) {
      await this.debtModal.nameInput.clear();
      await this.debtModal.nameInput.fill(updatedData.name);
    }
    if (updatedData.description !== undefined) {
      await this.debtModal.descriptionInput.clear();
      await this.debtModal.descriptionInput.fill(updatedData.description);
    }
    if (updatedData.interestRate !== undefined) {
      await this.debtModal.interestRateInput.clear();
      await this.debtModal.interestRateInput.fill(updatedData.interestRate);
    }
    await this.debtModal.submitAndExpectClosed();
    await this.page.waitForTimeout(1000);
  }

  // --- Delete Actions ---

  async deleteDebtFromTable(debtName: string): Promise<void> {
    const debtRow = this.debtsPage.getDebtRowByName(debtName);
    // Click the delete button (last button in actions cell)
    const deleteButton = debtRow.locator("td:last-child button").last();
    await deleteButton.click();
    await this.deleteModal.expectModal();
    await this.deleteModal.confirm();
    await this.page.waitForTimeout(1000);
  }

  async deleteDebtFromSidePanel(): Promise<void> {
    const deleteButton = this.debtsPage.sidePanel.locator("button").filter({ hasText: /delete/i }).first();
    await deleteButton.click();
    await this.deleteModal.expectModal();
    await this.deleteModal.confirm();
    await this.page.waitForTimeout(1000);
  }

  // --- Summary Stats ---

  async expectSummaryStripVisible(): Promise<void> {
    // KPI strip should be visible with 4 cards
    const kpiCards = this.page.locator(".grid.grid-cols-2 > div, .grid.lg\\:grid-cols-4 > div");
    await expect(kpiCards.first()).toBeVisible({ timeout: 10000 });
  }

  // --- Table Assertions ---

  async expectDebtListVisible(): Promise<void> {
    await expect(this.debtsPage.debtTable).toBeVisible({ timeout: 10000 });
  }

  async expectDebtTableRowCount(count: number): Promise<void> {
    await expect(this.debtsPage.debtTableRows).toHaveCount(count, { timeout: 10000 });
  }
}
