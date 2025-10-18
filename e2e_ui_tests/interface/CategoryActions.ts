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

// Category Statistics Actions
  async expectStatisticsVisible({
    totalCategories,
    expenseCategories,
    incomeCategories,
    parentCategories,
    childCategories
  }: {
    totalCategories?: number,
    expenseCategories?: number,
    incomeCategories?: number,
    parentCategories?: number,
    childCategories?: number
  }){
    await expect(this.categoryPage.getByTestId('total-categories-stat')).toBeVisible()
    await expect(this.categoryPage.getByTestId('expense-categories-stat')).toBeVisible()
    await expect(this.categoryPage.getByTestId('income-categories-stat')).toBeVisible()
    await expect(this.categoryPage.getByTestId('parent-categories-stat')).toBeVisible()
    await expect(this.categoryPage.getByTestId('child-categories-stat')).toBeVisible()
    if(totalCategories){
      await expect(this.categoryPage.getByTestId('total-categories-stat-value')).toContainText(totalCategories.toString())
    }
    if(expenseCategories){
      await expect(this.categoryPage.getByTestId('expense-categories-stat-value')).toContainText(expenseCategories.toString())
    }
    if(incomeCategories){
      await expect(this.categoryPage.getByTestId('income-categories-stat-value')).toContainText(incomeCategories.toString())
    }
    if(parentCategories){
      await expect(this.categoryPage.getByTestId('parent-categories-stat-value')).toContainText(parentCategories.toString())
    }
    if(childCategories){
      await expect(this.categoryPage.getByTestId('child-categories-stat-value')).toContainText(childCategories.toString())
    }
  }


// Create Category Actions

  async createCategory({name, type, parentCategoryName}:CategoryData){
    await this.openCreateCategoryModal()
    await this.createCategoryModal.fillForm({name, type, parentCategoryName})
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('hidden')
  }

  async createCategoryAndExpectFailure({name, type, parentCategoryName, toastErrorMessage, formErrorMessage, nameError}: CreateCategoryFailureData){
    await this.openCreateCategoryModal()
    await this.createCategoryModal.fillForm({name, type, parentCategoryName})
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('visible')
    if(toastErrorMessage){
      await this.createCategoryModal.expectErrorToast(toastErrorMessage)
    }
    if(formErrorMessage){
      await this.createCategoryModal.expectFormError(formErrorMessage)
    }
    if(nameError){
      await this.createCategoryModal.expectNameError(nameError)
    }
  }

  async expectCategoryTypeSelectState(type: 'EXPENSE' | 'INCOME', state: 'disabled' | 'enabled'){
    const categoryType = this.createCategoryModal.categoryTypeSelect
    state === 'disabled' ? await expect(categoryType).toBeDisabled() : await expect(categoryType).toBeEnabled()
    await expect(categoryType).toHaveValue(type)
  }

  async openCreateCategoryModal(){
    await this.categoryPage.createCategoryButton.click()
    await this.createCategoryModal.expectModal()
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


  // Edit Category Actions

  async editCategory(categoryName: string, updatedData: Partial<CategoryData>){
    await this.openEditCategoryModal(categoryName)
    await this.createCategoryModal.fillForm(updatedData)
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('hidden')
  }

  async editCategoryAndExpectFailure(
    {categoryName, updatedData, toastErrorMessage, formErrorMessage, nameError}: {
      categoryName: string, 
      updatedData: Partial<CategoryData>,
      toastErrorMessage?: string,
      formErrorMessage?: string,
      nameError?: string
    }
  ){
    await this.openEditCategoryModal(categoryName)
    await this.createCategoryModal.fillForm(updatedData)
    await this.createCategoryModal.submitButton.click()
    await this.expectCreateModalState('visible')
    if(toastErrorMessage){
      await this.createCategoryModal.expectErrorToast(toastErrorMessage)
    }
    if(formErrorMessage){
      await this.createCategoryModal.expectFormError(formErrorMessage)
    }
    if(nameError){
      await this.createCategoryModal.expectNameError(nameError)
    }
  }


  async expectCreateModalState(state?: 'hidden' | 'visible'){
    const exp =  expect(this.createCategoryModal.modal)
    state === 'hidden' ?await exp.toBeHidden() : await exp.toBeVisible()
  }

  async openEditCategoryModal(categoryName: string){
    await this.categoryPage.getCategoryItem(categoryName).getByTestId('category-edit-button').click()
    await this.createCategoryModal.expectModal()
  }



// Delete Category Actions

  async deleteCategory(categoryName: string){
    const category = this.categoryPage.getCategoryItem(categoryName)
    await category.getByTestId('delete-button').click()
  }

  async deleteCategoryAndExpectFailure(categoryName: string, toastErrorMessage: string, formErrorMessage: string, nameError: string){
    const category = this.categoryPage.getCategoryItem(categoryName)
    await category.getByTestId('delete-button').click()
    if(toastErrorMessage){
      await this.createCategoryModal.expectErrorToast(toastErrorMessage)
    }
    if(formErrorMessage){
      await this.createCategoryModal.expectFormError(formErrorMessage)
    }
  }

  async expectCategoryDeleted(categoryName: string){
    await expect(this.categoryPage.getCategoryItem(categoryName)).toBeHidden()
  }
}
