import { test, expect } from '@playwright/test';
import { AuthActions } from './interface/AuthActions';
import { CategoryActions } from './interface/CategoryActions';
import { ExpenseActions } from './interface/ExpenseActions';
import { NavigationActions } from './interface/NavigationActions';

// Define interfaces locally
interface UserCredentials {
  email: string;
  password: string;
}

interface CategoryData {
  name: string;
  description?: string;
  type: 'expense' | 'income';
  color?: string;
}

interface ExpenseData {
  amount: number;
  description: string;
  category: string;
  date: string;
  account?: string;
  tags?: string[];
}

// Test data
const testUser: UserCredentials = {
  email: 'test@example.com',
  password: 'password123'
};

const testCategory: CategoryData = {
  name: 'Test Expense Category',
  description: 'A test category for expenses',
  type: 'expense',
  color: '#FF5733'
};

const testExpense: ExpenseData = {
  amount: 100.50,
  description: 'Test Expense',
  category: 'Test Expense Category',
  date: '2024-01-15',
  tags: ['test', 'automation']
};

const testExpenseLarge: ExpenseData = {
  amount: 999.99,
  description: 'Large Test Expense',
  category: 'Test Expense Category',
  date: '2024-01-16'
};

test.describe('Expense Management', () => {
  let auth: AuthActions;
  let category: CategoryActions;
  let expense: ExpenseActions;
  let navigation: NavigationActions;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    category = new CategoryActions(page);
    expense = new ExpenseActions(page);
    navigation = new NavigationActions(page);
    await auth.login(testUser);
    
    // Create test category first
    await navigation.goto('category');
    await category.openCreateModal();
    await category.fillForm(testCategory);
    await category.save();
    await category.expectCreateModalHidden();
    await category.expectCategoryVisible(testCategory.name);
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: Delete test expenses and category
    try {
      await userActions.deleteExpense(testExpense.description);
    } catch (error) {
      // Expense might not exist, ignore error
    }
    
    try {
      await userActions.deleteExpense(testExpenseLarge.description);
    } catch (error) {
      // Expense might not exist, ignore error
    }
    
    try {
      await userActions.deleteCategory(testCategory.name);
    } catch (error) {
      // Category might not exist, ignore error
    }
  });

  test('should create a new expense', async ({ page }) => {
    await userActions.navigateToPage('expense');

    // Open create expense modal
    await page.getByTestId('create-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeVisible();

    // Fill expense form
    await page.getByTestId('expense-amount-input').fill(testExpense.amount.toString());
    await page.getByTestId('expense-description-input').fill(testExpense.description);
    
    // Select category
    await page.getByTestId('expense-category-select').click();
    await page.getByTestId(`category-option-${testCategory.name.toLowerCase().replace(/\s+/g, '-')}`).click();
    
    // Set date
    await page.getByTestId('expense-date-input').fill(testExpense.date!);
    
    // Add tags
    await page.getByTestId('expense-tags-input').fill(testExpense.tags!.join(', '));

    // Save expense
    await page.getByTestId('save-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeHidden();

    // Verify expense was created
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    
    // Verify expense details
    const expenseElement = page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`);
    await expect(expenseElement.getByTestId('expense-description')).toContainText(testExpense.description);
    await expect(expenseElement.getByTestId('expense-amount')).toContainText(testExpense.amount.toString());
    await expect(expenseElement.getByTestId('expense-category')).toContainText(testCategory.name);
  });

  test('should create expense using user actions', async ({ page }) => {
    await userActions.navigateToPage('expense');

    // Create expense using user actions
    await userActions.createExpense(testExpense);

    // Verify expense was created
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
  });

  test('should edit an existing expense', async ({ page }) => {
    // Create expense first
    await userActions.createExpense(testExpense);
    await userActions.navigateToPage('expense');

    // Edit expense
    const updatedAmount = 150.75;
    const updatedDescription = 'Updated Test Expense';
    
    await userActions.editExpense(testExpense.description, {
      amount: updatedAmount,
      description: updatedDescription
    });

    // Verify expense was updated
    await expect(page.getByTestId(`expense-item-${updatedDescription.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeHidden();
  });

  test('should delete an expense', async ({ page }) => {
    // Create expense first
    await userActions.createExpense(testExpense);
    await userActions.navigateToPage('expense');

    // Verify expense exists
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();

    // Delete expense
    await userActions.deleteExpense(testExpense.description);

    // Verify expense was deleted
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeHidden();
  });

  test('should search expenses', async ({ page }) => {
    // Create multiple expenses
    await userActions.createExpense(testExpense);
    await userActions.createExpense(testExpenseLarge);
    await userActions.navigateToPage('expense');

    // Search for specific expense
    await page.getByTestId('expense-search').fill('Test Expense');
    await page.keyboard.press('Enter');

    // Verify only matching expense is shown
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    await expect(page.getByTestId(`expense-item-${testExpenseLarge.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeHidden();

    // Clear search
    await page.getByTestId('expense-search').clear();
    await page.keyboard.press('Enter');

    // Verify all expenses are shown again
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    await expect(page.getByTestId(`expense-item-${testExpenseLarge.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
  });

  test('should filter expenses by category', async ({ page }) => {
    // Create expenses
    await userActions.createExpense(testExpense);
    await userActions.createExpense(testExpenseLarge);
    await userActions.navigateToPage('expense');

    // Filter by category
    await userActions.filterExpensesByCategory(testCategory.name);

    // Verify only expenses from the selected category are shown
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    await expect(page.getByTestId(`expense-item-${testExpenseLarge.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();

    // Clear filters
    await page.getByTestId('expense-filter-button').click();
    await page.getByTestId('clear-filter-button').click();
  });

  test('should filter expenses by date range', async ({ page }) => {
    // Create expenses with different dates
    await userActions.createExpense(testExpense);
    await userActions.createExpense(testExpenseLarge);
    await userActions.navigateToPage('expense');

    // Filter by date range
    await userActions.filterExpensesByDateRange('2024-01-15', '2024-01-15');

    // Verify only expenses within the date range are shown
    await expect(page.getByTestId(`expense-item-${testExpense.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeVisible();
    await expect(page.getByTestId(`expense-item-${testExpenseLarge.description.toLowerCase().replace(/\s+/g, '-')}`)).toBeHidden();
  });

  test('should validate required fields in expense creation', async ({ page }) => {
    await userActions.navigateToPage('expense');

    // Open create expense modal
    await page.getByTestId('create-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeVisible();

    // Try to save without filling required fields
    await page.getByTestId('save-expense-button').click();

    // Verify validation errors
    await expect(page.getByTestId('expense-amount-input-error')).toBeVisible();
    await expect(page.getByTestId('expense-description-input-error')).toBeVisible();
    await expect(page.getByTestId('expense-category-input-error')).toBeVisible();

    // Verify save button is disabled
    const saveButton = page.getByTestId('save-expense-button');
    await expect(saveButton).toBeDisabled();
  });

  test('should validate amount format', async ({ page }) => {
    await userActions.navigateToPage('expense');

    // Open create expense modal
    await page.getByTestId('create-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeVisible();

    // Try invalid amount formats
    const invalidAmounts = ['abc', '-50', '0', '100.999'];

    for (const amount of invalidAmounts) {
      await page.getByTestId('expense-amount-input').clear();
      await page.getByTestId('expense-amount-input').fill(amount);
      
      // Trigger validation by clicking save button
      await page.getByTestId('save-expense-button').click();
      
      // Verify error message appears
      await expect(page.getByTestId('expense-amount-input-error')).toBeVisible();
    }
  });

  test('should show expense statistics and totals', async ({ page }) => {
    // Create expenses first
    await userActions.createExpense(testExpense);
    await userActions.createExpense(testExpenseLarge);
    await userActions.navigateToPage('expense');

    // Switch to dashboard view
    await page.getByTestId('expense-dashboard-tab').click();
    await expect(page.getByTestId('expense-dashboard')).toBeVisible();

    // Verify total amount is displayed
    await expect(page.getByTestId('total-expense-amount')).toBeVisible();
    
    // Verify expense count
    await expect(page.getByTestId('total-expense-count')).toBeVisible();
    
    // Verify charts are displayed
    await expect(page.getByTestId('expense-chart')).toBeVisible();
    await expect(page.getByTestId('category-breakdown-chart')).toBeVisible();
  });

  test('should sort expenses by different columns', async ({ page }) => {
    // Create multiple expenses
    await userActions.createExpense(testExpense);
    await userActions.createExpense(testExpenseLarge);
    await userActions.navigateToPage('expense');

    // Switch to table view
    await page.getByTestId('expense-table-tab').click();
    await expect(page.getByTestId('expense-list')).toBeVisible();

    // Sort by amount
    await page.getByTestId('sort-amount').click();
    await page.waitForLoadState('networkidle');

    // Sort by date
    await page.getByTestId('sort-date').click();
    await page.waitForLoadState('networkidle');

    // Sort by category
    await page.getByTestId('sort-category').click();
    await page.waitForLoadState('networkidle');

    // Sort by description
    await page.getByTestId('sort-description').click();
    await page.waitForLoadState('networkidle');
  });

  test('should cancel expense creation', async ({ page }) => {
    await userActions.navigateToPage('expense');

    // Open create expense modal
    await page.getByTestId('create-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeVisible();

    // Fill some data
    await page.getByTestId('expense-amount-input').fill('100');
    await page.getByTestId('expense-description-input').fill('Cancel Test Expense');

    // Cancel creation
    await page.getByTestId('cancel-expense-button').click();
    await expect(page.getByTestId('create-expense-modal')).toBeHidden();

    // Verify expense was not created
    await expect(page.getByTestId('expense-item-cancel-test-expense')).toBeHidden();
  });

  test('should handle expense creation with special characters', async ({ page }) => {
    const specialExpense: ExpenseData = {
      amount: 99.99,
      description: 'Expense with Special Ch@rs! & Symbols',
      category: testCategory.name,
      date: '2024-01-15',
      tags: ['tëst', 'émojis 🎉']
    };

    await userActions.navigateToPage('expense');
    await userActions.createExpense(specialExpense);

    // Verify expense was created despite special characters
    const expenseTestId = `expense-item-${specialExpense.description.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
    await expect(page.getByTestId(expenseTestId)).toBeVisible();

    // Cleanup
    await userActions.deleteExpense(specialExpense.description);
  });

  test('should export expenses', async ({ page }) => {
    // Create expenses first
    await userActions.createExpense(testExpense);
    await userActions.navigateToPage('expense');

    // Set up download handling
    const downloadPromise = page.waitForEvent('download');

    // Export expenses as CSV
    await page.getByTestId('export-expenses-button').click();
    await expect(page.getByTestId('export-modal')).toBeVisible();
    await page.getByTestId('export-csv').click();

    // Wait for download
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');
  });
});

