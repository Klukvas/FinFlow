import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export interface PaymentFormData {
  amount: string;
  paymentDate?: string;
  description?: string;
}

export class PaymentModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
  }

  get amountInput() {
    return this.modal.locator('input[placeholder="0.00"]').first();
  }

  get paymentDateInput() {
    return this.modal.locator("#payment_date");
  }

  get descriptionInput() {
    return this.modal.locator("#description");
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
    await expect(this.amountInput).toBeVisible();
  }

  async fillForm(data: PaymentFormData): Promise<void> {
    await this.amountInput.clear();
    await this.amountInput.fill(data.amount);

    if (data.paymentDate) {
      await this.paymentDateInput.fill(data.paymentDate);
    }

    if (data.description) {
      await this.descriptionInput.clear();
      await this.descriptionInput.fill(data.description);
    }
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
