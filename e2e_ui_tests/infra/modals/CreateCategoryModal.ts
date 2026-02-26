import { Locator, Page, expect } from "@playwright/test";
import { BasePage } from "../BasePage";
import { CategoryData } from "../../types";

export class CreateCategoryModal extends BasePage {
  modal: Locator;
  nameInput: Locator;
  categoryTypeSelect: Locator;
  categoryParentSelect: Locator;
  closeButton: Locator;
  submitButton: Locator;
  errorToast: Locator;
  formError: Locator;
  nameError: Locator;
  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId("category-modal");
    this.nameInput = this.modal.getByTestId("category-name-input");
    this.nameError = this.modal.getByTestId("category-name-error");
    this.categoryTypeSelect = this.modal.getByTestId("category-type-select");
    this.categoryParentSelect = this.modal.getByTestId(
      "category-parent-select",
    );
    this.closeButton = this.modal.getByTestId("modal-close-button");
    this.submitButton = this.modal.getByTestId("submit-category");
    this.errorToast = this.page.getByTestId("error-toast");
    this.formError = this.modal.getByTestId("category-form-error");
  }
  async expectErrorToast(errorMessage?: string): Promise<void> {
    await expect(this.errorToast).toBeVisible();
    if (errorMessage) {
      await expect(this.errorToast).toContainText(errorMessage, {
        ignoreCase: true,
      });
    }
  }

  async expectNameError(errorMessage?: string): Promise<void> {
    await expect(this.nameError).toBeVisible();
    if (errorMessage) {
      await expect(this.nameError).toContainText(errorMessage, {
        ignoreCase: true,
      });
    }
  }

  async expectFormError(errorMessage?: string): Promise<void> {
    await expect(this.formError).toBeVisible();
    if (errorMessage) {
      await expect(this.formError).toContainText(errorMessage, {
        ignoreCase: true,
      });
    }
  }

  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible();
    await expect(this.categoryTypeSelect).toBeVisible();
    await expect(this.categoryParentSelect).toBeVisible();
    await expect(this.closeButton).toBeVisible();
  }

  async fillForm({ name, type, parentCategoryName }: Partial<CategoryData>) {
    if (name !== undefined) {
      await this.nameInput.fill(name);
    }
    if (type) {
      await this.categoryTypeSelect.selectOption(type);
    }
    if (parentCategoryName) {
      // Custom Select component: click trigger to open dropdown, then click option by text
      await this.categoryParentSelect.click();
      const dropdown = this.modal.locator('[data-testid="select-content"]');
      // CategorySelect uses data-testid="category-{id}" for each item
      const option = dropdown
        .locator('[data-testid^="category-"]')
        .filter({ hasText: parentCategoryName })
        .first();
      await option.click();
    }
  }
}
