import { test, expect } from '@playwright/test';
import { AuthActions } from '../interface/AuthActions';
import { CategoryActions } from '../interface/CategoryActions';
import { ExpenseActions } from '../interface/ExpenseActions';
import { NavigationActions } from '../interface/NavigationActions';

// All expense tests are skipped — the test infrastructure (ExpenseActions, page objects)
// needs to be implemented before these tests can run.
// TODO: Implement ExpenseActions methods (create, edit, delete, search, filter)
// TODO: Add proper test user login and data setup
test.describe.skip('Expense Management', () => {
  let auth: AuthActions;
  let category: CategoryActions;
  let expense: ExpenseActions;
  let navigation: NavigationActions;

  test('should create a new expense', async ({ page }) => {
    // Placeholder — needs ExpenseActions implementation
  });

  test('should edit an existing expense', async ({ page }) => {
    // Placeholder — needs ExpenseActions implementation
  });

  test('should delete an expense', async ({ page }) => {
    // Placeholder — needs ExpenseActions implementation
  });
});
