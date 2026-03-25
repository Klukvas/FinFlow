import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class GoalProgressModal extends BasePage {
  modal: Locator;
  amountInput: Locator;
  submitButton: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
    this.amountInput = this.modal.getByTestId("goal-progress-amount-input");
    this.submitButton = this.modal.getByTestId("goal-progress-submit");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.amountInput).toBeVisible();
  }

  async fillAmount(amount: string): Promise<void> {
    await this.amountInput.clear();
    await this.amountInput.fill(amount);
  }
}
