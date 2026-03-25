import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class GoalFormModal extends BasePage {
  modal: Locator;
  titleInput: Locator;
  descriptionInput: Locator;
  goalTypeSelect: Locator;
  prioritySelect: Locator;
  submitButton: Locator;
  closeButton: Locator;
  form: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
    this.form = this.modal.getByTestId("goal-form");
    this.titleInput = this.modal.getByTestId("goal-title-input");
    this.descriptionInput = this.modal.locator("#description");
    this.goalTypeSelect = this.modal.getByTestId("goal-type-select");
    this.prioritySelect = this.modal.getByTestId("goal-priority-select");
    this.submitButton = this.modal.getByTestId("goal-submit-button");
    this.closeButton = this.modal.getByTestId("modal-close-button");
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.form).toBeVisible();
    await expect(this.titleInput).toBeVisible();
  }

  async fillForm({
    title,
    description,
    goalType,
    priority,
    targetAmount,
  }: {
    title?: string;
    description?: string;
    goalType?: string;
    priority?: string;
    targetAmount?: string;
  }): Promise<void> {
    if (title !== undefined) {
      await this.titleInput.clear();
      await this.titleInput.fill(title);
    }
    if (description !== undefined) {
      await this.descriptionInput.clear();
      await this.descriptionInput.fill(description);
    }
    if (goalType) {
      await this.goalTypeSelect.selectOption(goalType);
    }
    if (priority) {
      await this.prioritySelect.selectOption(priority);
    }
    if (targetAmount) {
      // The target amount uses FormattedNumberInput (custom component)
      const amountInput = this.modal.locator(
        'input[placeholder="10000"]',
      );
      await amountInput.clear();
      await amountInput.fill(targetAmount);
    }
  }
}
