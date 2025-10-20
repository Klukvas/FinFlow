import test from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { CategoryApiActions } from "../interface/api/CategoryApiActions";
import { CategoryApiClient } from "../infra/api/CategoryApiClient";
import { UserApiActions } from "../interface/api/UserApiActions";
import { UserApiClient } from "../infra/api/UserApiClient";
import { users } from "../users";
import { generateCategory } from "../utils/generate-category";
import { CategoryActions } from "../interface/CategoryActions";
const user = users[0];

test.describe('Subscription', () => {
    let auth: AuthActions;
    let category: CategoryActions;
    let categoryApi: CategoryApiActions;
    let userApi: UserApiActions;
    let token: string;

    test.beforeAll(async () => {
        userApi = new UserApiActions(new UserApiClient('http://localhost:8001'));
        categoryApi = new CategoryApiActions(new CategoryApiClient('http://localhost:8002'));
    })

    test.beforeEach(async ({ page }) => {
        await page.goto('')
        auth = new AuthActions(page);
        category = new CategoryActions(page);
        token = await userApi.getToken(user.email, user.password);
    })

    test('should not allow to create more categories than the subscription allows', async ({ page }) => {
        const categories = await Promise.all(
            Array.from({ length: 15 }, () => generateCategory('EXPENSE'))
        );
        await categoryApi.createMultipleCategories(token, categories);
        await auth.login(user.email, user.password)
        const categoryData = await generateCategory('EXPENSE')
        await page.pause()
        await category.createCategoryAndExpectFailure({
          ...categoryData,
          toastErrorMessage: 'You have reached the maximum number of categories for your subscription',
          formErrorMessage: 'You have reached the maximum number of categories for your subscription',
          nameError: ''
        })
    })

})