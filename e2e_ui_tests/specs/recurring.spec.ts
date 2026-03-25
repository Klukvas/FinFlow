import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { RecurringActions } from "../interface/RecurringActions";
import { CategoryActions } from "../interface/CategoryActions";
import { SidebarInterface } from "../interface/SidebarInterface";
import { CategoryApiClient } from "../infra/api/CategoryApiClient";
import { CategoryApiActions, UserApiActions } from "../interface/api";
import { UserApiClient } from "../infra/api/UserApiClient";
import { generateCategory } from "../utils";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

test.describe("Recurring Payments Management", () => {
  let auth: AuthActions;
  let recurring: RecurringActions;
  let category: CategoryActions;
  let sidebar: SidebarInterface;
  let categoryApi: CategoryApiActions;
  let userApi: UserApiActions;

  // Store the created category name so tests can reference it
  let expenseCategoryName: string;

  test.beforeAll(async () => {
    userApi = new UserApiActions(new UserApiClient("http://localhost:8001"));
    categoryApi = new CategoryApiActions(
      new CategoryApiClient("http://localhost:8002"),
    );
  });

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    recurring = new RecurringActions(page);
    category = new CategoryActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);

    // Create an expense category (prerequisite for recurring payments)
    await sidebar.navigateToCategory();
    const categoryData = await generateCategory("EXPENSE");
    expenseCategoryName = categoryData.name;
    await category.createCategory(categoryData);
    await category.expectCategoryCreated(categoryData);

    // Navigate to recurring page
    await sidebar.navigateToRecurring();
  });

  test.describe("Create Recurring Payment", () => {
    test("should create a monthly recurring payment", async () => {
      const paymentName = `Monthly Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "1500",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 15,
        startDate: "2025-01-01",
        description: "Monthly test payment",
      });

      await recurring.expectPaymentVisible(paymentName);
    });
  });

  test.describe("View Recurring Payments", () => {
    test("should view recurring payments list", async () => {
      const paymentName = `List Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "2000",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 1,
        startDate: "2025-01-01",
      });

      await recurring.expectTableVisible();
      await recurring.expectPaymentVisible(paymentName);
    });

    test("should view upcoming executions", async () => {
      const paymentName = `Upcoming Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "500",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 1,
        startDate: "2025-01-01",
      });

      await recurring.expectUpcomingExecutionsVisible();
    });

    test("should view recurring statistics", async () => {
      const paymentName = `Stats Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "3000",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 10,
        startDate: "2025-01-01",
      });

      await recurring.expectSummaryStripVisible();
    });
  });

  test.describe("Pause and Resume", () => {
    test("should pause a recurring payment", async () => {
      const paymentName = `Pause Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "800",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 5,
        startDate: "2025-01-01",
      });

      await recurring.expectPaymentVisible(paymentName);
      await recurring.expectPaymentStatus(paymentName, "active");

      await recurring.pausePaymentFromTable(paymentName);

      await recurring.expectPaymentStatus(paymentName, "paused");
    });

    test("should resume a paused recurring payment", async () => {
      const paymentName = `Resume Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "600",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 20,
        startDate: "2025-01-01",
      });

      // First pause
      await recurring.pausePaymentFromTable(paymentName);
      await recurring.expectPaymentStatus(paymentName, "paused");

      // Then resume
      await recurring.resumePaymentFromTable(paymentName);
      await recurring.expectPaymentStatus(paymentName, "active");
    });
  });

  test.describe("Edit Recurring Payment", () => {
    test("should edit recurring payment details", async () => {
      const paymentName = `Edit Payment ${Date.now()}`;
      const updatedName = `Edited Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "1200",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 25,
        startDate: "2025-01-01",
        description: "Original description",
      });

      await recurring.expectPaymentVisible(paymentName);

      await recurring.editPaymentFromTable(paymentName, {
        name: updatedName,
        description: "Updated description",
      });

      await recurring.expectPaymentVisible(updatedName);
      await recurring.expectPaymentHidden(paymentName);
    });
  });

  test.describe("Delete Recurring Payment", () => {
    test("should delete a recurring payment", async () => {
      const paymentName = `Delete Payment ${Date.now()}`;

      await recurring.createRecurringPayment({
        name: paymentName,
        amount: "400",
        paymentType: "EXPENSE",
        categoryName: expenseCategoryName,
        scheduleType: "monthly",
        dayOfMonth: 28,
        startDate: "2025-01-01",
      });

      await recurring.expectPaymentVisible(paymentName);

      await recurring.deletePaymentFromTable(paymentName);

      await recurring.expectPaymentHidden(paymentName);
    });
  });
});
