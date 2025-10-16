import { test, expect } from '@playwright/test';
import { AuthActions } from '../interface/AuthActions';
import { CategoryActions } from '../interface/CategoryActions';
import { NavigationActions } from '../interface/NavigationActions';
import { SidebarInterface } from '../interface/SidebarInterface';
import { CategoryData } from '../types';
import { CategoryApiClient } from '../infra/api/CategoryApiClient';
import { CategoryApiActions, UserApiActions } from '../interface/api';
import { UserApiClient } from '../infra/api/UserApiClient';
// Define interfaces locally
interface UserCredentials {
  email: string;
  password: string;
}



// Test data
const testUser: UserCredentials = {
  email: 'root@root.root',
  password: 'Sololane56457!'
};

// Generate random suffix for test categories to avoid conflicts
const randomSuffix = Math.random().toString(36).substring(2, 8);

const testCategory: CategoryData = {
  name: `Test Category ${randomSuffix}`,
};

const testCategoryIncome: CategoryData = {
  name: `Test Income Category ${randomSuffix}`,
  type: 'Доходы',
};

test.describe('Category Management', () => {
  let auth: AuthActions;
  let category: CategoryActions;
  let navigation: NavigationActions;
  let sidebar: SidebarInterface;
  let categoryApi: CategoryApiActions;
  let userApi: UserApiActions;
  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    category = new CategoryActions(page);
    navigation = new NavigationActions(page);
    sidebar = new SidebarInterface(page);

    userApi = new UserApiActions(new UserApiClient('http://localhost:8001'));
    const token = await userApi.getToken(testUser.email, testUser.password);
    categoryApi = new CategoryApiActions(new CategoryApiClient('http://localhost:8002'));
    await categoryApi.deleteAllCategories(token);

    await page.goto('')
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToCategory();

  });

  test.afterEach(async ({ page }) => {
    // await category.delete(testCategory.name);
  });

  test.describe('Create Category', () => {
    test('should create a new expense category', async ({ page }) => {
      await category.createCategory({...testCategory})
      await category.expectCategoryCreated({...testCategory})
    });
  
    test('should create a new income category', async ({ page }) => {
      await category.createCategory({...testCategoryIncome})
      await category.expectCategoryCreated({...testCategoryIncome})
    });
  })

  test.describe('Edit Category', () => {
    test('should edit an existing category (name only)', async ({ page }) => {
      await category.createCategory({...testCategoryIncome})
      await category.expectCategoryCreated({...testCategoryIncome})
  
      const updatedCategory = {...testCategoryIncome, name: 'Updated Test Category'}
  
      await category.editCategory(testCategoryIncome.name, updatedCategory)
      await category.expectCategoryCreated(updatedCategory)
  
    });
  })

  

  

  test('should delete a category', async ({ page }) => {
  });

  test('should search categories', async ({ page }) => {
  });

  test('should validate required fields in category creation', async ({ page }) => {
  });

  test('should show category statistics', async ({ page }) => {
  });

  test('should handle category creation with special characters', async ({ page }) => {
  });

  test('should cancel category creation', async ({ page }) => {
  });

  test('should close category modal with close button', async ({ page }) => {
  });
});
