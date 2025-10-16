import { Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class CategoryPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Element selectors using data-testid
  get createCategoryButton() { return this.getByTestId('create-category-button'); }
  get categoryList() { return this.getByTestId('category-list'); }
  get categoryStats() { return this.getByTestId('category-statistics'); }
  get searchInput() { return this.getByTestId('category-search'); }
  get pageHeader() { return this.getByTestId('category-page-header'); }
  get totalCategories() { return this.getByTestId('total-categories'); }
  get expenseCategoriesCount() { return this.getByTestId('expense-categories-count'); }
  get incomeCategoriesCount() { return this.getByTestId('income-categories-count'); }

  // Helper method to get category item selector
  getCategoryItem(categoryName: string) {
    const testId = `table-category-${categoryName.toLowerCase().replace(/\s+/g, '-')}`
    return this.page.getByTestId(testId);
  }

  // Element expectations using expect
  async expectCategoryVisible(categoryName: string): Promise<void> {
    await expect(this.getCategoryItem(categoryName)).toBeVisible();
  }

  async expectCategoryHidden(categoryName: string): Promise<void> {
    await expect(this.getCategoryItem(categoryName)).toBeHidden();
  }

  async expectSearchResults(query: string): Promise<void> {
    // Verify that search results contain the query
    const results = this.page.locator('[data-testid^="category-item-"]');
    const count = await results.count();
    // This is a basic implementation - could be enhanced to verify actual content
    if (count === 0) {
      throw new Error(`No search results found for query: ${query}`);
    }
  }

  async expectAllCategoriesVisible(): Promise<void> {
    // Verify that categories list is populated
    await expect(this.page.locator('[data-testid^="category-item-"]').first()).toBeVisible();
  }

  async expectStatisticsVisible(): Promise<void> {
    await expect(this.categoryStats).toBeVisible();
  }

  async expectTotalCountVisible(): Promise<void> {
    await expect(this.totalCategories).toBeVisible();
  }

  async expectExpenseCountVisible(): Promise<void> {
    await expect(this.expenseCategoriesCount).toBeVisible();
  }

  async expectIncomeCountVisible(): Promise<void> {
    await expect(this.incomeCategoriesCount).toBeVisible();
  }
}