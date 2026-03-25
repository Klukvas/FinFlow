import { Page, expect, Locator } from "@playwright/test";
import { BasePage } from "../BasePage";

export class CreateIncomeModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.locator('[data-testid="modal"]');
  }

  // Form fields - use the same ids as the CreateIncome component
  get amountInput() {
    return this.modal.locator('input[inputmode="decimal"]');
  }

  get descriptionInput() {
    return this.modal.locator("textarea#description");
  }

  get dateInput() {
    return this.modal.locator('input[type="date"]#date');
  }

  get accountSelect() {
    return this.modal.locator("select#account_id");
  }

  get categorySelectTrigger() {
    return this.modal.getByTestId("select-trigger");
  }

  get submitButton() {
    return this.modal.locator('button[type="submit"]');
  }

  get closeButton() {
    return this.modal.getByTestId("modal-close-button");
  }

  async expectModalVisible(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.amountInput).toBeVisible();
  }

  async expectModalHidden(): Promise<void> {
    await expect(this.modal).toBeHidden();
  }

  async fillAmount(amount: string): Promise<void> {
    await this.amountInput.click();
    await this.amountInput.fill(amount);
  }

  async fillDescription(description: string): Promise<void> {
    await this.descriptionInput.fill(description);
  }

  async fillDate(date: string): Promise<void> {
    await this.dateInput.fill(date);
  }

  async selectAccount(accountName: string): Promise<void> {
    await this.accountSelect.selectOption({ label: new RegExp(accountName) });
  }

  async selectCategory(categoryName: string): Promise<void> {
    await this.categorySelectTrigger.click();
    const dropdown = this.page.getByTestId("select-content");
    await expect(dropdown).toBeVisible();
    const option = dropdown
      .locator('[data-testid^="category-"]')
      .filter({ hasText: categoryName })
      .first();
    await option.click();
  }

  async selectNoCategory(): Promise<void> {
    await this.categorySelectTrigger.click();
    const dropdown = this.page.getByTestId("select-content");
    await expect(dropdown).toBeVisible();
    const noneOption = dropdown.getByTestId("category-none");
    await noneOption.click();
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  async waitForModalClose(): Promise<void> {
    await expect(this.modal).toBeHidden({ timeout: 15000 });
  }

  async fillForm(data: {
    amount: string;
    description?: string;
    date?: string;
    categoryName?: string;
    accountName?: string;
  }): Promise<void> {
    await this.fillAmount(data.amount);

    if (data.categoryName) {
      await this.selectCategory(data.categoryName);
    }

    if (data.accountName) {
      await this.selectAccount(data.accountName);
    }

    if (data.description) {
      await this.fillDescription(data.description);
    }

    if (data.date) {
      await this.fillDate(data.date);
    }
  }
}
