import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";
import { AccountFormData } from "./CreateAccountModal";

export class EditAccountModal extends BasePage {
  modal: Locator;
  nameInput: Locator;
  typeSelect: Locator;
  submitButton: Locator;
  closeButton: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("edit-account-modal");
    this.nameInput = this.modal.getByTestId("account-name-input");
    this.typeSelect = this.modal.getByTestId("account-type-select");
    this.submitButton = this.modal.getByTestId("submit-account-button");
    this.closeButton = this.modal.getByTestId("modal-close-button");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible();
    await expect(this.typeSelect).toBeVisible();
    await expect(this.submitButton).toBeVisible();
  }

  async fillForm(data: Partial<AccountFormData>): Promise<void> {
    if (data.name !== undefined) {
      await this.nameInput.clear();
      await this.nameInput.fill(data.name);
    }
    if (data.type) {
      await this.typeSelect.selectOption(data.type);
    }
  }
}
