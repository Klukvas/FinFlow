import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { DebtActions } from "../interface/DebtActions";
import { SidebarInterface } from "../interface/SidebarInterface";
import { UserApiActions } from "../interface/api";
import { UserApiClient } from "../infra/api/UserApiClient";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

test.describe("Debts Management", () => {
  let auth: AuthActions;
  let debts: DebtActions;
  let sidebar: SidebarInterface;
  let userApi: UserApiActions;

  test.beforeAll(async () => {
    userApi = new UserApiActions(new UserApiClient("http://localhost:8001"));
  });

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    debts = new DebtActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToDebts();
  });

  test.describe("Contacts", () => {
    test("should create a contact", async () => {
      const contactName = `Test Contact ${Date.now()}`;

      await debts.createContact({
        name: contactName,
        email: "contact@test.com",
        phone: "+380501234567",
        company: "Test Company",
      });

      await debts.expectContactVisible(contactName);
    });
  });

  test.describe("Create Debt", () => {
    test("should create a debt (I owe - negative amount)", async () => {
      const debtName = `I Owe Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "5000",
        interestRate: "12.5",
        startDate: "2025-01-15",
        dueDate: "2026-01-15",
        description: "Test debt - I owe",
      });

      await debts.expectDebtVisible(debtName);
    });

    test("should create a debt (Owed to me - positive amount)", async () => {
      const debtName = `Owed To Me ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "3000",
        startDate: "2025-02-01",
        description: "Test debt - owed to me",
      });

      await debts.expectDebtVisible(debtName);
    });
  });

  test.describe("View Debts", () => {
    test("should view debt list", async ({ page }) => {
      const debtName = `List View Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "1000",
        startDate: "2025-03-01",
      });

      await debts.expectDebtListVisible();
      await debts.expectDebtVisible(debtName);
    });

    test("should view debt summary stats", async () => {
      const debtName = `Stats Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "2500",
        startDate: "2025-04-01",
      });

      await debts.expectSummaryStripVisible();
    });
  });

  test.describe("Payments", () => {
    test("should make a payment on a debt", async () => {
      const debtName = `Payment Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "10000",
        startDate: "2025-01-01",
      });

      await debts.expectDebtVisible(debtName);

      await debts.makePaymentFromTable(debtName, {
        amount: "1000",
        paymentDate: "2025-06-01",
        description: "First payment",
      });

      // Verify the debt still shows in the list (balance should have changed)
      await debts.expectDebtVisible(debtName);
    });

    test("should view payment history in side panel", async () => {
      const debtName = `Payment History Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "8000",
        startDate: "2025-01-01",
      });

      await debts.makePaymentFromTable(debtName, {
        amount: "500",
        paymentDate: "2025-05-01",
      });

      // Open the side panel to view payment history
      await debts.openDebtSidePanel(debtName);
      await debts.expectPaymentHistoryInSidePanel();
      await debts.expectPaymentCountInSidePanel(1);
      await debts.closeSidePanel();
    });
  });

  test.describe("Edit Debt", () => {
    test("should edit debt details", async () => {
      const debtName = `Edit Debt ${Date.now()}`;
      const updatedName = `Edited Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "4000",
        startDate: "2025-03-01",
        description: "Original description",
      });

      await debts.expectDebtVisible(debtName);

      await debts.editDebtFromTable(debtName, {
        name: updatedName,
        description: "Updated description",
      });

      await debts.expectDebtVisible(updatedName);
      await debts.expectDebtHidden(debtName);
    });
  });

  test.describe("Delete Debt", () => {
    test("should delete a debt", async () => {
      const debtName = `Delete Debt ${Date.now()}`;

      await debts.createDebt({
        name: debtName,
        initialAmount: "1500",
        startDate: "2025-05-01",
      });

      await debts.expectDebtVisible(debtName);

      await debts.deleteDebtFromTable(debtName);

      await debts.expectDebtHidden(debtName);
    });
  });
});
