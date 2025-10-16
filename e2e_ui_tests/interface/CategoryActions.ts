import { expect, Page } from '@playwright/test';
import { CategoryPage } from '../infra/pages/CategoryPage';
import { CreateCategoryModal } from '../infra/modals/CreateCategoryModal';
import { CategoryData, CreateCategoryFailureData } from '../types';

export class CategoryActions {
  private categoryPage: CategoryPage;
  private createCategoryModal: CreateCategoryModal;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.categoryPage = new CategoryPage(page);
    this.createCategoryModal = new CreateCategoryModal(page);
  }

  async openCreateCategoryModal(){
    await this.categoryPage.createCategoryButton.click()
    await this.createCategoryModal.expectModal()
  }

  async createCategory({name, type, parentCategoryName}:CategoryData){
    await this.openCreateCategoryModal()
    await this.createCategoryModal.fillForm({name, type, parentCategoryName})
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('hidden')
  }

  async createCategoryAndExpectFailure({name, type, parentCategoryName, toastErrorMessage, formErrorMessage}: CreateCategoryFailureData){
    await this.openCreateCategoryModal()
    await this.createCategoryModal.fillForm({name, type, parentCategoryName})
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('visible')
    await this.createCategoryModal.expectErrorToast(toastErrorMessage)
    await this.createCategoryModal.expectFormError(formErrorMessage)
  }

  async expectCreateModalState(state?: 'hidden' | 'visible'){
    const exp =  expect(this.createCategoryModal.modal)
    state === 'hidden' ?await exp.toBeHidden() : await exp.toBeVisible()
  }


  async editCategory(categoryName: string, updatedData: CategoryData){
    await this.categoryPage.getCategoryItem(categoryName).getByTestId('category-edit-button').click()
    await this.page.pause()
    await this.createCategoryModal.fillForm(updatedData)
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('hidden')
  }

  async expectCategoryCreated(category: CategoryData){
    const createdCategory = this.categoryPage.getCategoryItem(category.name)
    await expect(createdCategory).toBeVisible()
    await expect(createdCategory.getByTestId('category-name')).toContainText(category.name)
    await expect(createdCategory.getByTestId('category-type')).toContainText(category.type, {ignoreCase: true})
    if(category.parentCategoryName){
      await expect(createdCategory.getByTestId('category-parent-name')).toContainText(category.parentCategoryName)
    }
    else{
      await expect(createdCategory.getByTestId('category-parent-name')).toContainText('Root Category')
    }
    await expect(createdCategory.getByTestId('category-id')).not.toBeEmpty()
  }

}