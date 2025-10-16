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

const expenceRootCategory: CategoryData = {
  name: `Test Category ${randomSuffix}`,
  type: 'EXPENSE'
};

const childExpenceCategory: CategoryData = {
  name: `Child Test Category ${randomSuffix}`,
  type: 'EXPENSE',
  parentCategoryName: expenceRootCategory.name
};

const incomeRootCategory: CategoryData = {
  name: `Income Root Category ${randomSuffix}`,
  type: 'INCOME',
};

const incomeRootCategory2: CategoryData = {
  name: `Income Root Category 2 ${randomSuffix}`,
  type: 'INCOME',
};

const childIncomeCategory: CategoryData = {
  name: `Child Income Category ${randomSuffix}`,
  type: 'INCOME',
  parentCategoryName: incomeRootCategory.name
};



test.describe('Category Management', () => {
  let auth: AuthActions;
  let category: CategoryActions;
  let navigation: NavigationActions;
  let sidebar: SidebarInterface;
  let categoryApi: CategoryApiActions;
  let userApi: UserApiActions;

  test.beforeAll(async () => {
    userApi = new UserApiActions(new UserApiClient('http://localhost:8001'));
    categoryApi = new CategoryApiActions(new CategoryApiClient('http://localhost:8002'));
  })
  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    category = new CategoryActions(page);
    navigation = new NavigationActions(page);
    sidebar = new SidebarInterface(page);

    const token = await userApi.getToken(testUser.email, testUser.password);
    
    await categoryApi.deleteAllCategories(token);

    await page.goto('')
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToCategory();

  });

  test.afterEach(async () => {
  });

  test.describe('Create Category', () => {
    
    test.describe('Happy Path', () => {
      test('should create a new expense category', async ({ page }) => {
        await category.createCategory({...expenceRootCategory})
        await category.expectCategoryCreated({...expenceRootCategory})
      });
    
      test('should create a new income category', async ({ page }) => {
        await category.createCategory({...incomeRootCategory})
        await category.expectCategoryCreated({...incomeRootCategory})
      });

      test('should create a new expense category with parent category', async ({}) => {
        await category.createCategory({...expenceRootCategory})
        await category.expectCategoryCreated({...expenceRootCategory})

        await category.createCategory({...childExpenceCategory})
        await category.expectCategoryCreated({...childExpenceCategory})

      })

      test('should create a new income category with parent category', async ({}) => {
        await category.createCategory({...incomeRootCategory})
        await category.expectCategoryCreated({...incomeRootCategory})

        await category.createCategory({...childIncomeCategory})
        await category.expectCategoryCreated({...childIncomeCategory})

      })
    })

    test.describe('Unhappy Path', () => {
      test('should not create a category with the same name', async ({page}) => {
        await category.createCategory({...expenceRootCategory})
        await category.expectCategoryCreated({...expenceRootCategory})

        await category.createCategoryAndExpectFailure({
          ...expenceRootCategory, 
          toastErrorMessage: `Category name '${expenceRootCategory.name}' already exists for this user`, 
          formErrorMessage: 'Error creating category'
        })

      })
      test('should not create a category with the same name (different category type)', async ({page}) => {
        await category.createCategory({...expenceRootCategory})
        await category.expectCategoryCreated({...expenceRootCategory})

        await category.createCategoryAndExpectFailure({
          ...expenceRootCategory,
          type: 'INCOME',
          toastErrorMessage: `Category name '${expenceRootCategory.name}' already exists for this user`, 
          formErrorMessage: 'Error creating category'
        })

      })
      test('should not create a category with an empty name', async ({page}) => {
        await category.createCategoryAndExpectFailure({
          ...expenceRootCategory,
          name: '',
          nameError: 'Category name is required'
        })

      })
    })

  })

  test.describe('Edit Category', () => {

    test.describe('Happy Path', () => {
      test('should edit an existing category (name only)', async () => {
        await category.createCategory({...incomeRootCategory})
        await category.expectCategoryCreated({...incomeRootCategory})
    
        const updatedCategory = {...incomeRootCategory, name: 'Updated Test Category'}
    
        await category.editCategory(incomeRootCategory.name, updatedCategory)
        await category.expectCategoryCreated(updatedCategory)
    
      });

      test('type should be read-only', async () => {
        await category.createCategory({...incomeRootCategory})
        await category.expectCategoryCreated({...incomeRootCategory})
        await category.openEditCategoryModal(incomeRootCategory.name)
        await category.expectCategoryTypeSelectState('INCOME', 'disabled')
      });

      test('should add parent category', async () => {
        await category.createCategory({...incomeRootCategory})
        await category.expectCategoryCreated({...incomeRootCategory})

        await category.createCategory({...incomeRootCategory2})
        await category.expectCategoryCreated({...incomeRootCategory2})

        await category.editCategory(incomeRootCategory2.name, {parentCategoryName: incomeRootCategory.name})
        await category.expectCategoryCreated({...incomeRootCategory2, parentCategoryName: incomeRootCategory.name})
      });


    })


  })

  

  

  test('should delete a category', async () => {
  });

  test('should search categories', async () => {
  });

  test('should validate required fields in category creation', async () => {
  });

  test('should show category statistics', async () => {
  });

  test('should handle category creation with special characters', async () => {
  });

  test('should cancel category creation', async () => {
  });

  test('should close category modal with close button', async () => {
  });
});
