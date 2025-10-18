import { test, expect } from '@playwright/test';
import { AuthActions } from '../interface/AuthActions';
import { CategoryActions } from '../interface/CategoryActions';
import { NavigationActions } from '../interface/NavigationActions';
import { SidebarInterface } from '../interface/SidebarInterface';
import { CategoryData } from '../types';
import { CategoryApiClient } from '../infra/api/CategoryApiClient';
import { CategoryApiActions, UserApiActions } from '../interface/api';
import { UserApiClient } from '../infra/api/UserApiClient';
import { generateCategory } from '../utils';
interface UserCredentials {
  email: string;
  password: string;
}



// Test data
const testUser: UserCredentials = {
  email: 'root@root.root',
  password: 'Sololane56457!'
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
        const categoryData = await generateCategory('EXPENSE')
        await category.createCategory({...categoryData})
        await category.expectCategoryCreated({...categoryData})
      });
    
      test('should create a new income category', async ({ page }) => {
        const categoryData = await generateCategory('INCOME')
        await category.createCategory({...categoryData})
        await category.expectCategoryCreated({...categoryData})
      });

      test('should create a new expense category with parent category', async ({}) => {
        const categoryData = await generateCategory('EXPENSE')
        await category.createCategory({...categoryData})
        await category.expectCategoryCreated({...categoryData})

        const childCategoryData = await generateCategory('EXPENSE', categoryData.name)
        await category.createCategory({...childCategoryData})
        await category.expectCategoryCreated({...childCategoryData})

      })

      test('should create a new income category with parent category', async ({}) => {
        const categoryData = await generateCategory('INCOME')
        await category.createCategory({...categoryData})
        await category.expectCategoryCreated({...categoryData})

        const childCategoryData = await generateCategory('INCOME', categoryData.name)
        await category.createCategory({...childCategoryData})
        await category.expectCategoryCreated({...childCategoryData})

      })

      test('should show category statistics after creation', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        const expenceCategoryData = await generateCategory('EXPENSE')
        await category.createCategory({...expenceCategoryData})
        await category.expectCategoryCreated({...expenceCategoryData})

        await category.expectStatisticsVisible({
          totalCategories: 2,
          expenseCategories: 1,
          incomeCategories: 1,
          parentCategories: 2,
          childCategories: 0
        })
      });
    })

    test.describe('Unhappy Path', () => {
      test('should not create a category with the same name', async ({page}) => {
        const expenceCategoryData = await generateCategory('EXPENSE')
        await category.createCategory({...expenceCategoryData})
        await category.expectCategoryCreated({...expenceCategoryData})

        await category.createCategoryAndExpectFailure({
          ...expenceCategoryData, 
          toastErrorMessage: `Category name already exists for this user`, 
          formErrorMessage: 'Category name already exists for this user'
        })

      })
      test('should not create a category with the same name (different category type)', async ({page}) => {
        const expenceCategoryData = await generateCategory('EXPENSE')
        await category.createCategory({...expenceCategoryData})
        await category.expectCategoryCreated({...expenceCategoryData})
        await category.createCategoryAndExpectFailure({
          ...expenceCategoryData,
          type: 'INCOME',
          toastErrorMessage: `Category name already exists for this user`, 
          formErrorMessage: 'Category name already exists for this user'
        })

      })
      test('should not create a category with an empty name', async ({page}) => {
        const expenceCategoryData = await generateCategory('EXPENSE')
        await category.createCategoryAndExpectFailure({
          ...expenceCategoryData,
          name: '',
          nameError: 'Category name is required'
        })

      })
      test('should not create a category with a third parent category', async ({page}) => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        const incomeCategoryData2 = await generateCategory('INCOME', incomeCategoryData.name)
        await category.createCategory({...incomeCategoryData2})
        await category.expectCategoryCreated({...incomeCategoryData2})
        
        const incomeCategoryData3 = await generateCategory('INCOME', incomeCategoryData.name)

        await category.createCategoryAndExpectFailure({
          ...incomeCategoryData3,
          parentCategoryName: incomeCategoryData2.name,
          toastErrorMessage: 'Maximum category depth of 2 levels exceeded. Categories can only have 2 levels: Root → Level 1 → Level 2 (max)',
          formErrorMessage: 'Maximum category depth of 2 levels exceeded. Categories can only have 2 levels: Root → Level 1 → Level 2 (max)'
        })
        
      })
    })

  })

  test.describe('Edit Category', () => {

    test.describe('Happy Path', () => {
      test('should edit an existing category (name only)', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})
    
        const updatedCategory = {...incomeCategoryData, name: 'Updated Test Category'}
    
        await category.editCategory(incomeCategoryData.name, {name: updatedCategory.name})
        await category.expectCategoryCreated(updatedCategory)
    
      });

      test('type should be read-only', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})
        await category.openEditCategoryModal(incomeCategoryData.name)
        await category.expectCategoryTypeSelectState('INCOME', 'disabled')
      });

      test('should add parent category', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        const incomeCategoryData2 = await generateCategory('INCOME', incomeCategoryData.name)
        
        await category.createCategory({...incomeCategoryData2})
        await category.expectCategoryCreated({...incomeCategoryData2})

        await category.editCategory(incomeCategoryData2.name, {parentCategoryName: incomeCategoryData.name})
        await category.expectCategoryCreated({...incomeCategoryData2, parentCategoryName: incomeCategoryData.name})
      });


    })

    test.describe('Unhappy Path', () => {
      test('should not edit a category with an empty name', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        await category.editCategoryAndExpectFailure({
          categoryName: incomeCategoryData.name,
          updatedData: {name: ''},
          nameError: 'Category name is required'
        })
      });

      test('should not edit the category with third parent category', async ({page}) => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        const incomeCategoryData2 = await generateCategory('INCOME', incomeCategoryData.name)
        await category.createCategory({...incomeCategoryData2})
        await category.expectCategoryCreated({...incomeCategoryData2})

        const incomeCategoryData3 = await generateCategory('INCOME', incomeCategoryData.name)
        await category.createCategory({...incomeCategoryData3})
        await category.expectCategoryCreated({...incomeCategoryData3})
        await page.pause();

        await category.editCategoryAndExpectFailure(
          {categoryName: incomeCategoryData3.name,
          updatedData: {parentCategoryName: incomeCategoryData2.name},
          toastErrorMessage: 'Maximum category depth of 2 levels exceeded. Categories can only have 2 levels: Root → Level 1 → Level 2 (max)',
          formErrorMessage: 'Maximum category depth of 2 levels exceeded. Categories can only have 2 levels: Root → Level 1 → Level 2 (max)'
        })
      })

    })


  })

  test.describe('Delete Category', () => {
    test.describe('Happy Path', () => {
      test('should delete a category', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})
        
        await category.expectStatisticsVisible({
          totalCategories: 1,
          expenseCategories: 0,
          incomeCategories: 1,
          parentCategories: 1,
          childCategories: 0
        })


        await category.deleteCategory(incomeCategoryData.name)
        await category.expectCategoryDeleted(incomeCategoryData.name)

        await category.expectStatisticsVisible({
          totalCategories: 0,
          expenseCategories: 0,
          incomeCategories: 0,
          parentCategories: 0,
          childCategories: 0
        })
      })
    })
    test.describe('Unhappy Path', () => {
      test('should not delete a category with children', async () => {
        const incomeCategoryData = await generateCategory('INCOME')
        await category.createCategory({...incomeCategoryData})
        await category.expectCategoryCreated({...incomeCategoryData})

        const childIncomeCategoryData = await generateCategory('INCOME', incomeCategoryData.name)
        await category.createCategory({...childIncomeCategoryData})
        await category.expectCategoryCreated({...childIncomeCategoryData})

        await category.deleteCategoryAndExpectFailure(
          incomeCategoryData.name,
          'Cannot delete category with child categories. Delete children first.',
          '',
          ''
        )
      })
    })
  })
});
