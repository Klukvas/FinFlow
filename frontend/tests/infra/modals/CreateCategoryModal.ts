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
  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId('category-modal')
    this.nameInput = this.modal.getByTestId('category-name-input')
    this.categoryTypeSelect = this.modal.getByTestId('category-type-select')
    this.categoryParentSelect = this.modal.getByTestId('category-parent-select')
    this.closeButton = this.modal.getByTestId('modal-close-button')
    this.submitButton = this.modal.getByTestId('submit-category')
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
      await this.categoryParentSelect.selectOption(parentCategoryName)
    }
  }
}