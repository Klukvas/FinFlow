import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { IncomeActions } from "../interface/IncomeActions";
import { SidebarInterface } from "../interface/SidebarInterface";
import {
  CategoryApiActions,
  UserApiActions,
  IncomeApiActions,
  AccountApiActions,
} from "../interface/api";
import { CategoryApiClient } from "../infra/api/CategoryApiClient";
import { UserApiClient } from "../infra/api/UserApiClient";
import { IncomeApiClient } from "../infra/api/IncomeApiClient";
import { AccountApiClient } from "../infra/api/AccountApiClient";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

let incomeCategoryName: string;
let incomeCategoryId: number;
let testAccountName: string;
let testAccountId: number;
let initialAccountBalance: number;

test.describe("Income Management", () => {
  let auth: AuthActions;
  let income: IncomeActions;
  let sidebar: SidebarInterface;
  let userApi: UserApiActions;
  let categoryApi: CategoryApiActions;
  let incomeApi: IncomeApiActions;
  let accountApi: AccountApiActions;
  let token: string;
  let workspaceId: string;

  test.beforeAll(async () => {
    userApi = new UserApiActions(new UserApiClient("http://localhost:8001"));
    categoryApi = new CategoryApiActions(
      new CategoryApiClient("http://localhost:8002"),
    );
    incomeApi = new IncomeApiActions(
      new IncomeApiClient("http://localhost:8004/incomes"),
    );
    accountApi = new AccountApiActions(
      new AccountApiClient("http://localhost:8005/accounts"),
    );

    token = await userApi.getToken(testUser.email, testUser.password);
    workspaceId = userApi.getWorkspaceIdFromToken(token);

    // Clean up existing data
    await incomeApi.deleteAllIncomes(token, workspaceId);
    await categoryApi.deleteAllCategories(token, workspaceId);
    await accountApi.deleteAllAccounts(token, workspaceId);

    // Create test income category via API
    const catClient = new CategoryApiClient("http://localhost:8002");
    catClient.setToken(token);
    catClient.setWorkspaceId(workspaceId);
    const catResponse = await catClient.createCategory({
      name: "E2E Income Category",
      type: "INCOME",
    });
    if (catResponse.error || !catResponse.data) {
      throw new Error(`Failed to create test category: ${catResponse.error}`);
    }
    incomeCategoryName = catResponse.data.name;
    incomeCategoryId = catResponse.data.id;

    // Create test account via API
    initialAccountBalance = 5000;
    const account = await accountApi.createAccount(
      token,
      {
        name: "E2E Income Account",
        balance: initialAccountBalance,
        currency: "USD",
        account_type: "checking",
      },
      workspaceId,
    );
    testAccountName = account.name;
    testAccountId = account.id;
  });

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    income = new IncomeActions(page);
    sidebar = new SidebarInterface(page);

    // Clean up incomes before each test
    await incomeApi.deleteAllIncomes(token, workspaceId);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToIncome();
    await page.waitForLoadState("networkidle");
  });

  test.describe("Create Income", () => {
    test("should create income with category", async () => {
      await income.createIncome({
        amount: "2500",
        description: "Monthly salary",
        categoryName: incomeCategoryName,
      });

      await income.expectIncomeVisible("2 500");
      await income.expectIncomeVisible(incomeCategoryName);
    });
  });

  test.describe("Edit Income", () => {
    test("should edit income via delete and re-create", async ({ page }) => {
      // Income page does not have an edit button (only delete).
      // Verify we can delete and re-create with updated data.
      await income.createIncome({
        amount: "1000",
        description: "Original income",
        categoryName: incomeCategoryName,
      });
      await income.expectIncomeVisible("1 000");

      // Delete the old income
      await income.deleteIncome("1 000");
      await income.expectIncomeNotVisible("1 000");

      // Re-create with updated values
      await income.createIncome({
        amount: "1500",
        description: "Updated income",
        categoryName: incomeCategoryName,
      });
      await income.expectIncomeVisible("1 500");
    });
  });

  test.describe("Delete Income", () => {
    test("should delete an income", async () => {
      await income.createIncome({
        amount: "800",
        description: "Income to delete",
        categoryName: incomeCategoryName,
      });
      await income.expectIncomeVisible("800");

      await income.deleteIncome("800");

      await income.expectIncomeNotVisible("800");
    });
  });

  test.describe("Income List", () => {
    test("should view income list", async () => {
      // Create a few incomes via API
      const incClient = new IncomeApiClient("http://localhost:8004/incomes");
      incClient.setToken(token);
      incClient.setWorkspaceId(workspaceId);

      await incClient.createIncome({
        amount: 500,
        description: "Income entry 1",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: incomeCategoryId,
      });

      await incClient.createIncome({
        amount: 750,
        description: "Income entry 2",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: incomeCategoryId,
      });

      // Reload the page
      await sidebar.navigateToIncome();

      await income.expectTableVisible();
      await income.expectTableRowCount(2);
    });

    test("should view income summary", async () => {
      await income.createIncome({
        amount: "3000",
        description: "Summary test income",
        categoryName: incomeCategoryName,
      });

      await income.expectSummaryStripVisible();
    });
  });

  test.describe("Filter Income", () => {
    test("should filter income by category", async () => {
      // Create a second income category via API
      const catClient = new CategoryApiClient("http://localhost:8002");
      catClient.setToken(token);
      catClient.setWorkspaceId(workspaceId);
      const cat2Response = await catClient.createCategory({
        name: "E2E Other Income Cat",
        type: "INCOME",
      });
      if (cat2Response.error || !cat2Response.data) {
        throw new Error(
          `Failed to create second category: ${cat2Response.error}`,
        );
      }
      const secondCategoryName = cat2Response.data.name;
      const secondCategoryId = cat2Response.data.id;

      // Create incomes in different categories via API
      const incClient = new IncomeApiClient("http://localhost:8004/incomes");
      incClient.setToken(token);
      incClient.setWorkspaceId(workspaceId);

      await incClient.createIncome({
        amount: 400,
        description: "Cat1 income",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: incomeCategoryId,
      });

      await incClient.createIncome({
        amount: 600,
        description: "Cat2 income",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: secondCategoryId,
      });

      // Reload page
      await sidebar.navigateToIncome();

      // Open filters
      await income.openFilters();

      // Filter by first category
      await income.filterByCategory(incomeCategoryName);

      // Should only show cat1 income
      await income.expectIncomeVisible(incomeCategoryName);
      await income.expectIncomeNotVisible(secondCategoryName);

      // Clean up second category
      try {
        await catClient.deleteCategory(secondCategoryId);
      } catch {
        // ignore cleanup errors
      }
    });
  });

  test.describe("Account Balance", () => {
    test("should increase account balance when income is created with account", async () => {
      // Get the initial balance
      const beforeBalance = await accountApi.getAccountBalance(
        token,
        testAccountId,
        workspaceId,
      );

      // Create income with account
      await income.createIncome({
        amount: "500",
        description: "Balance test income",
        categoryName: incomeCategoryName,
        accountName: testAccountName,
      });

      // Verify balance increased
      const afterBalance = await accountApi.getAccountBalance(
        token,
        testAccountId,
        workspaceId,
      );

      expect(afterBalance.balance).toBeGreaterThan(beforeBalance.balance);
      expect(afterBalance.balance - beforeBalance.balance).toBeCloseTo(500, 0);
    });
  });
});
