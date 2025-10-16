import { Locator, Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';
import { CategoryData } from '../../types';

export class CreateCategoryModal extends BasePage {
  modal: Locator
  nameInput: Locator
  categoryTypeSelect: Locator
  categoryParentSelect: Locator
  closeButton: Locator
  submitButton: Locator
  errorToast: Locator
  formError: Locator
  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId('category-modal')
    this.nameInput = this.modal.getByTestId('category-name-input')
    this.categoryTypeSelect = this.modal.getByTestId('category-type-select')
    this.categoryParentSelect = this.modal.getByTestId('category-parent-select')
    this.closeButton = this.modal.getByTestId('modal-close-button')
    this.submitButton = this.modal.getByTestId('submit-category')
    this.errorToast = this.page.getByTestId('error-toast')
    this.formError = this.modal.getByTestId('category-form-error')
  }
  async expectErrorToast(errorMessage?: string): Promise<void> {
    await expect(this.errorToast).toBeVisible()
    if(errorMessage){
      await expect(this.errorToast).toContainText(errorMessage, {ignoreCase: true})
    }
  }

  async expectFormError(errorMessage?: string): Promise<void> {
    await expect(this.formError).toBeVisible()
    if(errorMessage){
      await expect(this.formError).toContainText(errorMessage, {ignoreCase: true})
    }
  }


  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.nameInput).toBeVisible()
    await expect(this.categoryTypeSelect).toBeVisible()
    await expect(this.categoryParentSelect).toBeVisible()
    await expect(this.closeButton).toBeVisible()
  }

  async fillForm({name, type, parentCategoryName}: CategoryData){
    await this.nameInput.fill(name)
    if(type){
      await this.categoryTypeSelect.selectOption(type)
    }
    if(parentCategoryName){
      // Find the option by data-testid and get its value
      const optionTestId = `category-parent-option-${parentCategoryName.toLowerCase().replace(/\s+/g, '-')}`
      const option = this.modal.locator(`option[data-testid="${optionTestId}"]`)
      const value = await option.getAttribute('value')
      
      if (value) {
        await this.categoryParentSelect.selectOption(value)
      } else {
        throw new Error(`Could not find option with test-id: ${optionTestId}`)
      }
    }
  }
}