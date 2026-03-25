import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export interface AccountFormData {
  name?: string;
  type?: string;
  currency?: string;
  balance?: string;
}

export class CreateAccountModal extends BasePage {
  modal: Locator;
  nameInput: Locator;
  typeSelect: Locator;
  currencySelect: Locator;
  balanceInput: Locator;
  submitButton: Locator;
  closeButton: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("create-account-modal");
    this.nameInput = this.modal.getByTestId("account-name-input");
    this.typeSelect = this.modal.getByTestId("account-type-select");
    this.currencySelect = this.modal.getByTestId("account-currency-select");
    this.balanceInput = this.modal.getByTestId("account-balance-input");
    this.submitButton = this.modal.getByTestId("submit-account-button");
    this.closeButton = this.modal.getByTestId("modal-close-button");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible();
    await expect(this.typeSelect).toBeVisible();
    await expect(this.submitButton).toBeVisible();
  }

  async fillForm(data: AccountFormData): Promise<void> {
    if (data.name !== undefined) {
      await this.nameInput.fill(data.name);
    }
    if (data.type) {
      await this.typeSelect.selectOption(data.type);
    }
    if (data.currency) {
      await this.currencySelect.selectOption(data.currency);
    }
    if (data.balance !== undefined) {
      await this.balanceInput.fill(data.balance);
    }
  }
}
