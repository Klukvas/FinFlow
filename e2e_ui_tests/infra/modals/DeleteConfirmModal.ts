import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class DeleteConfirmModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
  }

  get confirmButton() {
    return this.modal.locator("button").filter({ hasText: /delete|confirm|remove/i });
  }

  get cancelButton() {
    return this.modal.locator("button").filter({ hasText: /cancel/i });
  }

  get closeButton() {
    return this.modal.getByTestId("modal-close-button");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.confirmButton).toBeVisible();
  }

  async confirm(): Promise<void> {
    await this.confirmButton.click();
    await expect(this.modal).toBeHidden({ timeout: 10000 });
  }

  async cancel(): Promise<void> {
    await this.cancelButton.click();
    await expect(this.modal).toBeHidden();
  }
}
