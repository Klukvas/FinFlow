import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { ExpenseActions } from "../interface/ExpenseActions";
import { SidebarInterface } from "../interface/SidebarInterface";
import { CategoryApiActions, UserApiActions, ExpenseApiActions, AccountApiActions } from "../interface/api";
import { CategoryApiClient } from "../infra/api/CategoryApiClient";
import { UserApiClient } from "../infra/api/UserApiClient";
import { ExpenseApiClient } from "../infra/api/ExpenseApiClient";
import { AccountApiClient } from "../infra/api/AccountApiClient";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

// Category and account names are created via API in beforeAll
let expenseCategoryName: string;
let expenseCategoryId: number;
let testAccountName: string;
let testAccountId: number;
let initialAccountBalance: number;

test.describe("Expense Management", () => {
  let auth: AuthActions;
  let expense: ExpenseActions;
  let sidebar: SidebarInterface;
  let userApi: UserApiActions;
  let categoryApi: CategoryApiActions;
  let expenseApi: ExpenseApiActions;
  let accountApi: AccountApiActions;
  let token: string;
  let workspaceId: string;

  test.beforeAll(async () => {
    userApi = new UserApiActions(new UserApiClient("http://localhost:8001"));
    categoryApi = new CategoryApiActions(
      new CategoryApiClient("http://localhost:8002"),
    );
    expenseApi = new ExpenseApiActions(
      new ExpenseApiClient("http://localhost:8003/expenses"),
    );
    accountApi = new AccountApiActions(
      new AccountApiClient("http://localhost:8005/accounts"),
    );

    token = await userApi.getToken(testUser.email, testUser.password);
    workspaceId = userApi.getWorkspaceIdFromToken(token);

    // Clean up existing data
    await expenseApi.deleteAllExpenses(token, workspaceId);
    await categoryApi.deleteAllCategories(token, workspaceId);
    await accountApi.deleteAllAccounts(token, workspaceId);

    // Create test category via API
    const catClient = new CategoryApiClient("http://localhost:8002");
    catClient.setToken(token);
    catClient.setWorkspaceId(workspaceId);
    const catResponse = await catClient.createCategory({
      name: "E2E Expense Category",
      type: "EXPENSE",
    });
    if (catResponse.error || !catResponse.data) {
      throw new Error(`Failed to create test category: ${catResponse.error}`);
    }
    expenseCategoryName = catResponse.data.name;
    expenseCategoryId = catResponse.data.id;

    // Create test account via API
    initialAccountBalance = 10000;
    const account = await accountApi.createAccount(token, {
      name: "E2E Test Account",
      balance: initialAccountBalance,
      currency: "USD",
      account_type: "checking",
    }, workspaceId);
    testAccountName = account.name;
    testAccountId = account.id;
  });

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    expense = new ExpenseActions(page);
    sidebar = new SidebarInterface(page);

    // Clean up expenses before each test
    await expenseApi.deleteAllExpenses(token, workspaceId);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToExpense();
    await page.waitForLoadState("networkidle");
  });

  test.describe("Create Expense", () => {
    test("should create an expense with category", async () => {
      await expense.createExpense({
        amount: "150",
        description: "Groceries shopping",
        categoryName: expenseCategoryName,
      });

      await expense.expectExpenseVisible("150");
      await expense.expectExpenseVisible(expenseCategoryName);
    });

    test("should create an expense without category", async () => {
      await expense.createExpense({
        amount: "75",
        description: "Miscellaneous purchase",
      });

      await expense.expectExpenseVisible("75");
    });
  });

  test.describe("Edit Expense", () => {
    test("should edit expense amount and description", async () => {
      // Create an expense first
      await expense.createExpense({
        amount: "200",
        description: "Original expense",
        categoryName: expenseCategoryName,
      });
      await expense.expectExpenseVisible("200");

      // Edit it
      await expense.editExpense("200", {
        amount: "350",
        description: "Updated expense",
      });

      await expense.expectExpenseVisible("350");
    });
  });

  test.describe("Delete Expense", () => {
    test("should delete an expense", async () => {
      // Create an expense first
      await expense.createExpense({
        amount: "500",
        description: "Expense to delete",
        categoryName: expenseCategoryName,
      });
      await expense.expectExpenseVisible("500");

      // Delete it
      await expense.deleteExpense("500");

      // Verify it is gone
      await expense.expectExpenseNotVisible("500");
    });
  });

  test.describe("Expense List", () => {
    test("should view expense list with pagination", async () => {
      // Create 11 expenses to trigger pagination (page size is 10)
      const expClient = new ExpenseApiClient("http://localhost:8003/expenses");
      expClient.setToken(token);
      expClient.setWorkspaceId(workspaceId);

      for (let i = 1; i <= 11; i++) {
        await expClient.createExpense({
          amount: 10 + i,
          description: `Paginated expense ${i}`,
          date: new Date().toISOString().split("T")[0],
          currency: "USD",
          category_id: expenseCategoryId,
        });
      }

      // Reload the page to see all expenses
      await sidebar.navigateToExpense();
      await expense.expectTableVisible();
      // Default page size is 10, so first page should have 10 rows
      await expense.expectTableRowCount(10);
      await expense.expectPaginationVisible();
    });

    test("should view expense summary strip", async () => {
      // Create an expense so summary strip has data
      await expense.createExpense({
        amount: "300",
        description: "Summary test expense",
        categoryName: expenseCategoryName,
      });

      await expense.expectSummaryStripVisible();
    });
  });

  test.describe("Filter Expenses", () => {
    test("should filter expenses by category", async () => {
      // Create a second category via API
      const catClient = new CategoryApiClient("http://localhost:8002");
      catClient.setToken(token);
      catClient.setWorkspaceId(workspaceId);
      const cat2Response = await catClient.createCategory({
        name: "E2E Other Expense Cat",
        type: "EXPENSE",
      });
      if (cat2Response.error || !cat2Response.data) {
        throw new Error(`Failed to create second category: ${cat2Response.error}`);
      }
      const secondCategoryName = cat2Response.data.name;
      const secondCategoryId = cat2Response.data.id;

      // Create expenses in different categories via API
      const expClient = new ExpenseApiClient("http://localhost:8003/expenses");
      expClient.setToken(token);
      expClient.setWorkspaceId(workspaceId);

      await expClient.createExpense({
        amount: 100,
        description: "Cat1 expense",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: expenseCategoryId,
      });

      await expClient.createExpense({
        amount: 200,
        description: "Cat2 expense",
        date: new Date().toISOString().split("T")[0],
        currency: "USD",
        category_id: secondCategoryId,
      });

      // Reload page
      await sidebar.navigateToExpense();

      // Open filters
      await expense.openFilters();

      // Filter by first category
      await expense.filterByCategory(expenseCategoryName);

      // Should only show cat1 expense
      await expense.expectExpenseVisible(expenseCategoryName);
      await expense.expectExpenseNotVisible(secondCategoryName);

      // Clean up second category
      try {
        await catClient.deleteCategory(secondCategoryId);
      } catch {
        // ignore cleanup errors
      }
    });
  });

  test.describe("Account Balance", () => {
    test("should reduce account balance when expense is created with account", async () => {
      // Get the initial balance
      const beforeBalance = await accountApi.getAccountBalance(
        token,
        testAccountId,
        workspaceId,
      );

      // Create expense with account
      await expense.createExpense({
        amount: "100",
        description: "Balance test expense",
        categoryName: expenseCategoryName,
        accountName: testAccountName,
      });

      // Verify balance decreased
      const afterBalance = await accountApi.getAccountBalance(
        token,
        testAccountId,
        workspaceId,
      );

      expect(afterBalance.balance).toBeLessThan(beforeBalance.balance);
      expect(beforeBalance.balance - afterBalance.balance).toBeCloseTo(100, 0);
    });
  });
});
