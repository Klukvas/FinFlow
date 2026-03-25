import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export interface DebtFormData {
  name: string;
  debtType?: string;
  description?: string;
  currency?: string;
  initialAmount: string;
  interestRate?: string;
  minimumPayment?: string;
  startDate?: string;
  dueDate?: string;
  contactName?: string;
}

export class DebtModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
  }

  get nameInput() {
    return this.modal.locator("#name");
  }

  get descriptionInput() {
    return this.modal.locator("#description");
  }

  get initialAmountInput() {
    return this.modal.locator('input[placeholder="0.00"]').first();
  }

  get interestRateInput() {
    return this.modal.locator("#interest_rate");
  }

  get startDateInput() {
    return this.modal.locator("#start_date");
  }

  get dueDateInput() {
    return this.modal.locator("#due_date");
  }

  get submitButton() {
    return this.modal.locator('button[type="submit"]');
  }

  get cancelButton() {
    return this.modal.locator('button[type="button"]').filter({ hasText: /cancel/i });
  }

  get closeButton() {
    return this.modal.getByTestId("modal-close-button");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible();
  }

  async fillForm(data: DebtFormData): Promise<void> {
    // Name
    await this.nameInput.clear();
    await this.nameInput.fill(data.name);

    // Initial amount
    if (data.initialAmount) {
      await this.initialAmountInput.clear();
      await this.initialAmountInput.fill(data.initialAmount);
    }

    // Interest rate
    if (data.interestRate) {
      await this.interestRateInput.clear();
      await this.interestRateInput.fill(data.interestRate);
    }

    // Start date
    if (data.startDate) {
      await this.startDateInput.fill(data.startDate);
    }

    // Due date
    if (data.dueDate) {
      await this.dueDateInput.fill(data.dueDate);
    }

    // Description
    if (data.description) {
      await this.descriptionInput.clear();
      await this.descriptionInput.fill(data.description);
    }
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  async submitAndExpectClosed(): Promise<void> {
    await this.submitButton.click();
    await expect(this.modal).toBeHidden({ timeout: 10000 });
  }

  async close(): Promise<void> {
    await this.closeButton.click();
    await expect(this.modal).toBeHidden();
  }
}
