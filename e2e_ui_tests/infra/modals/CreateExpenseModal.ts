import { Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class CreateExpenseModal extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Element selectors using data-testid
  get modal() { return this.getByTestId('create-expense-modal'); }
  get modalTitle() { return this.getByTestId('create-expense-modal-title'); }
  get amountInput() { return this.getByTestId('expense-amount-input'); }
  get descriptionInput() { return this.getByTestId('expense-description-input'); }
  get categorySelect() { return this.getByTestId('expense-category-select'); }
  get dateInput() { return this.getByTestId('expense-date-input'); }
  get accountSelect() { return this.getByTestId('expense-account-select'); }
  get tagsInput() { return this.getByTestId('expense-tags-input'); }
  get saveButton() { return this.getByTestId('save-expense-button'); }
  get cancelButton() { return this.getByTestId('cancel-expense-button'); }
  get closeButton() { return this.getByTestId('modal-close-button'); }
  get errorMessage() { return this.getByTestId('create-expense-error'); }
  get amountInputError() { return this.getByTestId('expense-amount-input-error'); }
  get categoryInputError() { return this.getByTestId('expense-category-input-error'); }

  // Element expectations using expect
  async expectModalVisible(): Promise<void> {
    await expect(this.modal).toBeVisible();
  }

  async expectModalHidden(): Promise<void> {
    await expect(this.modal).toBeHidden();
  }

  async expectFormElementsVisible(): Promise<void> {
    await expect(this.amountInput).toBeVisible();
    await expect(this.categorySelect).toBeVisible();
    await expect(this.saveButton).toBeVisible();
  }

  async expectValidationErrors(): Promise<void> {
    await expect(this.amountInputError).toBeVisible();
  }

  async expectSaveButtonDisabled(): Promise<void> {
    await expect(this.saveButton).toBeDisabled();
  }
}