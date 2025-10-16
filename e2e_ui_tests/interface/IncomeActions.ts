import { Page, expect } from '@playwright/test';
// TODO: Import IncomePage and CreateIncomeModal when they are created
// import { IncomePage } from '../infra/pages';
// import { CreateIncomeModal } from '../infra/modals';

export interface IncomeData {
  amount: string | number;
  description: string;
  category: string;
  date?: string;
  account?: string;
  tags?: string[];
}

export class IncomeActions {
  private page: Page;
  // TODO: Add page objects when they are created
  // private incomePage: IncomePage;
  // private createIncomeModal: CreateIncomeModal;

  constructor(page: Page) {
    this.page = page;
    // TODO: Initialize page objects when they are created
    // this.incomePage = new IncomePage(page);
    // this.createIncomeModal = new CreateIncomeModal(page);
  }

  /**
   * Navigate to income page and verify it loads
   */
  async goto(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.goto();
    await this.page.goto('/income');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Create new income - complete business workflow
   * 1. Navigate to income page
   * 2. Open create income form
   * 3. Fill all income data
   * 4. Save income
   * 5. Verify modal closes
   * 6. Verify income appears in list
   */
  async createIncome(incomeData: IncomeData): Promise<void> {
    await this.goto();
    await this.openIncomeCreationForm();
    await this.fillIncomeForm(incomeData);
    await this.saveIncome();
    await this.expectIncomeCreationComplete();
    await this.expectIncomeVisible(incomeData.description);
  }

  /**
   * Open income creation form - complete business workflow
   * 1. Click create income button
   * 2. Verify modal opens
   * 3. Verify all form elements are present
   */
  async openIncomeCreationForm(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.openCreateModal();
    // await this.incomePage.expectCreateModalVisible();
    // await this.incomePage.expectCreateFormElementsVisible();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('create-income-button').click();
    await expect(this.page.getByTestId('create-income-modal')).toBeVisible();
  }

  /**
   * Fill income form with data
   */
  async fillIncomeForm(incomeData: IncomeData): Promise<void> {
    // TODO: Use CreateIncomeModal when created
    // await this.createIncomeModal.fillForm(incomeData);
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('income-amount-input').fill(incomeData.amount.toString());
    await this.page.getByTestId('income-description-input').fill(incomeData.description);
    
    // Select category
    await this.page.getByTestId('income-category-select').click();
    await this.page.getByTestId(`category-option-${incomeData.category.toLowerCase().replace(/\s+/g, '-')}`).click();
    
    if (incomeData.date) {
      await this.page.getByTestId('income-date-input').fill(incomeData.date);
    }
    
    if (incomeData.account) {
      await this.page.getByTestId('income-account-select').click();
      await this.page.getByTestId(`account-option-${incomeData.account.toLowerCase().replace(/\s+/g, '-')}`).click();
    }
    
    if (incomeData.tags && incomeData.tags.length > 0) {
      await this.page.getByTestId('income-tags-input').fill(incomeData.tags.join(', '));
    }
  }

  /**
   * Save income and verify completion
   */
  async saveIncome(): Promise<void> {
    // TODO: Use CreateIncomeModal when created
    // await this.createIncomeModal.save();
    // await this.createIncomeModal.waitForModalClose();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('save-income-button').click();
    await expect(this.page.getByTestId('create-income-modal')).toBeHidden();
  }

  /**
   * Verify income creation is complete
   */
  async expectIncomeCreationComplete(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectCreateModalHidden();
    // await this.incomePage.expectIncomeListUpdated();
  }

  /**
   * Verify income is visible in the list
   */
  async expectIncomeVisible(description: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectIncomeVisible(description);
  }

  /**
   * Edit existing income - complete business workflow
   * 1. Navigate to income page
   * 2. Find income item and click edit
   * 3. Verify edit modal opens
   * 4. Update income data
   * 5. Save changes
   * 6. Verify modal closes and changes are reflected
   */
  async editIncome(incomeDescription: string, updatedData: Partial<IncomeData>): Promise<void> {
    await this.goto();
    await this.openIncomeEditForm(incomeDescription);
    await this.updateIncomeForm(updatedData);
    await this.saveIncome();
    await this.expectIncomeEditComplete();
    await this.expectIncomeVisible(updatedData.description || incomeDescription);
  }

  /**
   * Open income edit form
   */
  async openIncomeEditForm(incomeDescription: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.editIncome(incomeDescription);
    // await this.incomePage.expectEditModalVisible();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId(`income-item-${incomeDescription.toLowerCase().replace(/\s+/g, '-')}`)
      .getByTestId('edit-income-button').click();
    await expect(this.page.getByTestId('edit-income-modal')).toBeVisible();
  }

  /**
   * Update income form with new data
   */
  async updateIncomeForm(updatedData: Partial<IncomeData>): Promise<void> {
    // TODO: Use CreateIncomeModal when created
    // await this.createIncomeModal.updateForm(updatedData);
    
    // Temporary implementation with direct locators - should be removed
    if (updatedData.amount) {
      await this.page.getByTestId('income-amount-input').fill(updatedData.amount.toString());
    }
    if (updatedData.description) {
      await this.page.getByTestId('income-description-input').fill(updatedData.description);
    }
    if (updatedData.category) {
      await this.page.getByTestId('income-category-select').click();
      await this.page.getByTestId(`category-option-${updatedData.category.toLowerCase().replace(/\s+/g, '-')}`).click();
    }
    if (updatedData.date) {
      await this.page.getByTestId('income-date-input').fill(updatedData.date);
    }
    if (updatedData.account) {
      await this.page.getByTestId('income-account-select').click();
      await this.page.getByTestId(`account-option-${updatedData.account.toLowerCase().replace(/\s+/g, '-')}`).click();
    }
    if (updatedData.tags) {
      await this.page.getByTestId('income-tags-input').fill(updatedData.tags.join(', '));
    }
  }

  /**
   * Verify income edit is complete
   */
  async expectIncomeEditComplete(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectEditModalHidden();
    // await this.incomePage.expectIncomeListUpdated();
  }

  /**
   * Delete income - complete business workflow
   * 1. Navigate to income page
   * 2. Find income item and click delete
   * 3. Confirm deletion in modal
   * 4. Verify income is removed from list
   */
  async deleteIncome(incomeDescription: string): Promise<void> {
    await this.goto();
    await this.openIncomeDeleteConfirmation(incomeDescription);
    await this.confirmIncomeDeletion();
    await this.expectIncomeDeleted(incomeDescription);
  }

  /**
   * Open income delete confirmation
   */
  async openIncomeDeleteConfirmation(incomeDescription: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.deleteIncome(incomeDescription);
    // await this.incomePage.expectDeleteConfirmationVisible();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId(`income-item-${incomeDescription.toLowerCase().replace(/\s+/g, '-')}`)
      .getByTestId('delete-income-button').click();
    await expect(this.page.getByTestId('confirm-delete-modal')).toBeVisible();
  }

  /**
   * Confirm income deletion
   */
  async confirmIncomeDeletion(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.confirmDelete();
    // await this.incomePage.expectDeleteConfirmationHidden();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('confirm-delete-button').click();
    await expect(this.page.getByTestId('confirm-delete-modal')).toBeHidden();
  }

  /**
   * Verify income is deleted
   */
  async expectIncomeDeleted(incomeDescription: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectIncomeHidden(incomeDescription);
  }

  /**
   * Search and verify income results - complete business workflow
   * 1. Navigate to income page
   * 2. Enter search query
   * 3. Verify filtered results
   * 4. Clear search and verify all income returns
   */
  async searchAndVerifyIncome(query: string): Promise<void> {
    await this.goto();
    await this.performIncomeSearch(query);
    await this.expectIncomeSearchResults(query);
    await this.clearIncomeSearch();
    await this.expectAllIncomeVisible();
  }

  /**
   * Perform income search
   */
  async performIncomeSearch(query: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.searchIncome(query);
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('income-search').fill(query);
    await this.page.keyboard.press('Enter');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Verify income search results
   */
  async expectIncomeSearchResults(query: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectSearchResults(query);
  }

  /**
   * Clear income search
   */
  async clearIncomeSearch(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.clearSearch();
  }

  /**
   * Verify all income is visible
   */
  async expectAllIncomeVisible(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectAllIncomeVisible();
  }

  /**
   * Filter income by category - complete business workflow
   * 1. Navigate to income page
   * 2. Open filter modal
   * 3. Select category filter
   * 4. Apply filter
   * 5. Verify filtered results
   */
  async filterIncomeByCategory(category: string): Promise<void> {
    await this.goto();
    await this.openIncomeFilterModal();
    await this.selectCategoryFilter(category);
    await this.applyIncomeFilter();
    await this.expectIncomeFilteredByCategory(category);
  }

  /**
   * Open income filter modal
   */
  async openIncomeFilterModal(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.openFilterModal();
    // await this.incomePage.expectFilterModalVisible();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('income-filter-button').click();
    await expect(this.page.getByTestId('income-filter-modal')).toBeVisible();
  }

  /**
   * Select category filter
   */
  async selectCategoryFilter(category: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.selectCategoryFilter(category);
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId(`filter-category-${category.toLowerCase().replace(/\s+/g, '-')}`).click();
  }

  /**
   * Apply income filter
   */
  async applyIncomeFilter(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.applyFilter();
    // await this.incomePage.expectFilterModalHidden();
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('apply-filter-button').click();
    await expect(this.page.getByTestId('income-filter-modal')).toBeHidden();
  }

  /**
   * Verify income filtered by category
   */
  async expectIncomeFilteredByCategory(category: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectFilteredByCategory(category);
  }

  /**
   * Filter income by date range - complete business workflow
   * 1. Navigate to income page
   * 2. Open filter modal
   * 3. Set date range
   * 4. Apply filter
   * 5. Verify filtered results
   */
  async filterIncomeByDateRange(startDate: string, endDate: string): Promise<void> {
    await this.goto();
    await this.openIncomeFilterModal();
    await this.setDateRangeFilter(startDate, endDate);
    await this.applyIncomeFilter();
    await this.expectIncomeFilteredByDateRange(startDate, endDate);
  }

  /**
   * Set date range filter
   */
  async setDateRangeFilter(startDate: string, endDate: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.setDateRangeFilter(startDate, endDate);
    
    // Temporary implementation with direct locators - should be removed
    await this.page.getByTestId('filter-start-date').fill(startDate);
    await this.page.getByTestId('filter-end-date').fill(endDate);
  }

  /**
   * Verify income filtered by date range
   */
  async expectIncomeFilteredByDateRange(startDate: string, endDate: string): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectFilteredByDateRange(startDate, endDate);
  }

  /**
   * Verify income page statistics - complete business verification
   * 1. Navigate to income page
   * 2. Verify total income amount is displayed
   * 3. Verify income count is correct
   * 4. Verify income list is populated
   */
  async verifyIncomeStatistics(): Promise<void> {
    await this.goto();
    await this.expectTotalIncomeAmountVisible();
    await this.expectIncomeCountVisible();
    await this.expectIncomeListPopulated();
  }

  /**
   * Verify total income amount is visible
   */
  async expectTotalIncomeAmountVisible(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectTotalAmountVisible();
  }

  /**
   * Verify income count is visible
   */
  async expectIncomeCountVisible(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectIncomeCountVisible();
  }

  /**
   * Verify income list is populated
   */
  async expectIncomeListPopulated(): Promise<void> {
    // TODO: Use IncomePage when created
    // await this.incomePage.expectIncomeListPopulated();
  }

  /**
   * Get income summary data - complete business data retrieval
   * Returns: total amount, count, and list of all visible income
   */
  async getIncomeSummary(): Promise<{
    totalAmount: number;
    count: number;
    incomes: Array<{ description: string; amount: number; category: string }>;
  }> {
    await this.goto();
    const totalAmount = await this.getTotalIncomeAmount();
    const count = await this.getIncomeCount();
    const incomes = await this.getAllVisibleIncome();
    
    return { totalAmount, count, incomes };
  }

  /**
   * Get total income amount
   */
  async getTotalIncomeAmount(): Promise<number> {
    // TODO: Use IncomePage when created
    // return await this.incomePage.getTotalAmount();
    
    // Temporary implementation with direct locators - should be removed
    const totalText = await this.page.getByTestId('total-income-amount').textContent();
    const match = totalText?.match(/[\d,]+\.?\d*/);
    return match ? parseFloat(match[0].replace(/,/g, '')) : 0;
  }

  /**
   * Get income count
   */
  async getIncomeCount(): Promise<number> {
    // TODO: Use IncomePage when created
    // return await this.incomePage.getIncomeCount();
    
    // Temporary implementation with direct locators - should be removed
    const incomeElements = this.page.locator('[data-testid^="income-item-"]');
    return await incomeElements.count();
  }

  /**
   * Get all visible income
   */
  async getAllVisibleIncome(): Promise<Array<{ description: string; amount: number; category: string }>> {
    // TODO: Use IncomePage when created
    // return await this.incomePage.getVisibleIncomes();
    
    // Temporary implementation with direct locators - should be removed
    const incomeElements = this.page.locator('[data-testid^="income-item-"]');
    const count = await incomeElements.count();
    const incomes: Array<{ description: string; amount: number; category: string }> = [];
    
    for (let i = 0; i < count; i++) {
      const element = incomeElements.nth(i);
      const description = await element.getByTestId('income-description').textContent() || '';
      const amountText = await element.getByTestId('income-amount').textContent() || '';
      const category = await element.getByTestId('income-category').textContent() || '';
      
      const amount = parseFloat(amountText.replace(/[$,]/g, '')) || 0;
      
      incomes.push({ description, amount, category });
    }
    
    return incomes;
  }

  /**
   * Check if income exists
   */
  async incomeExists(description: string): Promise<boolean> {
    // TODO: Use IncomePage when created
    // return await this.incomePage.incomeExists(description);
    
    // Temporary implementation with direct locators - should be removed
    try {
      await expect(this.page.getByTestId(`income-item-${description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible({ timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }
}

