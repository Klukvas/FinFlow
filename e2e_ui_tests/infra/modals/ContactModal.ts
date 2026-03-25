import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export interface ContactFormData {
  name: string;
  email?: string;
  phone?: string;
  company?: string;
}

export class ContactModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
  }

  get nameInput() {
    return this.modal.locator("#name");
  }

  get emailInput() {
    return this.modal.locator("#email");
  }

  get phoneInput() {
    return this.modal.locator("#phone");
  }

  get companyInput() {
    return this.modal.locator("#company");
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

  async fillForm(data: ContactFormData): Promise<void> {
    await this.nameInput.clear();
    await this.nameInput.fill(data.name);

    if (data.email) {
      await this.emailInput.clear();
      await this.emailInput.fill(data.email);
    }

    if (data.phone) {
      await this.phoneInput.clear();
      await this.phoneInput.fill(data.phone);
    }

    if (data.company) {
      await this.companyInput.clear();
      await this.companyInput.fill(data.company);
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
