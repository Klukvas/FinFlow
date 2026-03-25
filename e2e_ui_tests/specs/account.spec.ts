import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { AccountActions } from "../interface/AccountActions";
import { SidebarInterface } from "../interface/SidebarInterface";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

function generateAccountName(prefix: string): string {
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  return `${prefix} ${randomSuffix}`;
}

test.describe("Account Management", () => {
  let auth: AuthActions;
  let account: AccountActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    account = new AccountActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToAccount();
  });

  test.describe("View Account List", () => {
    test("should display the account page with header and summary", async () => {
      await account.expectPageVisible();
      await account.expectPageHeaderVisible();
      await account.expectSummaryStripVisible();
    });

    test("should display the account table", async () => {
      await account.expectTableVisible();
    });
  });

  test.describe("Create Account", () => {
    test("should create a new bank account", async () => {
      const accountName = generateAccountName("Bank Test");

      await account.createAccount({
        name: accountName,
        type: "bank",
        currency: "USD",
        balance: "1000",
      });

      await account.expectAccountInTable(accountName);
    });

    test("should create a new cash account", async () => {
      const accountName = generateAccountName("Cash Test");

      await account.createAccount({
        name: accountName,
        type: "cash",
        currency: "EUR",
        balance: "500",
      });

      await account.expectAccountInTable(accountName);
    });

    test("should show the created account in the account list", async () => {
      const accountName = generateAccountName("Verify List");

      await account.createAccount({
        name: accountName,
        type: "bank",
        currency: "USD",
        balance: "250",
      });

      // Verify it appears in the table
      await account.expectAccountInTable(accountName);
      // Verify the summary strip is still visible (counts may have updated)
      await account.expectSummaryStripVisible();
    });
  });

  test.describe("Edit Account", () => {
    test("should edit an account name", async () => {
      const originalName = generateAccountName("Edit Original");
      const updatedName = generateAccountName("Edit Updated");

      // Create account first
      await account.createAccount({
        name: originalName,
        type: "bank",
        currency: "USD",
        balance: "100",
      });
      await account.expectAccountInTable(originalName);

      // Edit the account
      await account.editAccount(originalName, { name: updatedName });

      // Verify the updated name appears
      await account.expectAccountInTable(updatedName);
      // Verify the old name is gone
      await account.expectAccountNotInTable(originalName);
    });
  });

  test.describe("Archive Account", () => {
    test("should archive an account", async () => {
      const accountName = generateAccountName("Archive Test");

      // Create account first
      await account.createAccount({
        name: accountName,
        type: "bank",
        currency: "USD",
        balance: "0",
      });
      await account.expectAccountInTable(accountName);

      // Archive the account
      await account.archiveAccount(accountName);

      // Archived accounts are filtered out from the active list
      await account.expectAccountNotInTable(accountName);
    });
  });
});
