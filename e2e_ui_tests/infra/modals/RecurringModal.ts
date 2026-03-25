import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export interface RecurringFormData {
  name: string;
  description?: string;
  amount: string;
  currency?: string;
  paymentType?: "EXPENSE" | "INCOME";
  scheduleType?: "daily" | "weekly" | "monthly" | "yearly";
  dayOfMonth?: number;
  startDate?: string;
  endDate?: string;
  categoryName?: string;
}

export class RecurringModal extends BasePage {
  readonly modal: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("modal");
  }

  get nameInput() {
    return this.modal.locator('input[type="text"]').first();
  }

  get descriptionInput() {
    return this.modal.locator("textarea").first();
  }

  get amountInput() {
    return this.modal.locator('input[placeholder="0.00"]').first();
  }

  get paymentTypeSelect() {
    return this.modal
      .locator("select")
      .filter({ has: this.page.locator('option[value="EXPENSE"]') })
      .first();
  }

  get scheduleTypeSelect() {
    return this.modal
      .locator("select")
      .filter({ has: this.page.locator('option[value="monthly"]') })
      .first();
  }

  get dayOfMonthInput() {
    return this.modal
      .locator('input[type="number"][min="1"][max="31"]')
      .first();
  }

  get startDateInput() {
    return this.modal.locator('input[type="date"]').first();
  }

  get endDateInput() {
    return this.modal.locator('input[type="date"]').nth(1);
  }

  get submitButton() {
    return this.modal.locator('button[type="submit"]');
  }

  get cancelButton() {
    return this.modal
      .locator('button[type="button"]')
      .filter({ hasText: /cancel/i });
  }

  get closeButton() {
    return this.modal.getByTestId("modal-close-button");
  }

  // Category selector - the CategorySelect component renders a label + select-trigger
  // We locate the parent container that has the "Category" label text, then find the trigger inside
  getCategoryTrigger(): Locator {
    // The CategorySelect renders inside a div.space-y-2, with a label containing "Category"
    // and a select-trigger button. We find the container with that label and get its trigger.
    const categoryContainer = this.modal
      .locator("label")
      .filter({ hasText: /category/i })
      .first()
      .locator("..");
    return categoryContainer.locator('[data-testid="select-trigger"]');
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible();
  }

  async fillForm(data: RecurringFormData): Promise<void> {
    // Name
    await this.nameInput.clear();
    await this.nameInput.fill(data.name);

    // Description
    if (data.description) {
      await this.descriptionInput.clear();
      await this.descriptionInput.fill(data.description);
    }

    // Amount
    if (data.amount) {
      await this.amountInput.clear();
      await this.amountInput.fill(data.amount);
    }

    // Payment type
    if (data.paymentType) {
      await this.paymentTypeSelect.selectOption(data.paymentType);
      // Wait for category list to reload after payment type change
      await this.page.waitForTimeout(500);
    }

    // Category - click the trigger and select an option by text
    if (data.categoryName) {
      const categoryTrigger = this.getCategoryTrigger();
      await categoryTrigger.click();
      // The select-content dropdown appears inside the same relative container
      const dropdown = this.modal
        .locator('[data-testid="select-content"]')
        .last();
      await expect(dropdown).toBeVisible({ timeout: 5000 });
      const option = dropdown
        .locator(`[data-testid^="category-"]`)
        .filter({ hasText: data.categoryName })
        .first();
      await option.click();
    }

    // Schedule type
    if (data.scheduleType) {
      await this.scheduleTypeSelect.selectOption(data.scheduleType);
    }

    // Day of month (for monthly schedule)
    if (data.dayOfMonth !== undefined) {
      await this.dayOfMonthInput.clear();
      await this.dayOfMonthInput.fill(data.dayOfMonth.toString());
    }

    // Start date
    if (data.startDate) {
      await this.startDateInput.fill(data.startDate);
    }

    // End date
    if (data.endDate) {
      await this.endDateInput.fill(data.endDate);
    }
  }

  async submitAndExpectClosed(): Promise<void> {
    await this.submitButton.click();
    await expect(this.modal).toBeHidden({ timeout: 15000 });
  }

  async close(): Promise<void> {
    await this.closeButton.click();
    await expect(this.modal).toBeHidden();
  }
}
