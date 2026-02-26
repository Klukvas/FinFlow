import { test, expect } from "@playwright/test";
import { AuthActions } from "../../interface/AuthActions";
import { NavigationActions } from "../../interface/NavigationActions";
import { SidebarInterface } from "../../interface/SidebarInterface";

const newUser = {
  email: `signup-test-${Date.now()}@example.com`,
  password: "SupaPupaStrongBibasPassword83218034!",
};

test.describe("Sign Up Flow", () => {
  let auth: AuthActions;
  let navigation: NavigationActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    await page.goto("");
    auth = new AuthActions(page);
    navigation = new NavigationActions(page);
    sidebar = new SidebarInterface(page);
  });

  test("should register new user", async ({ page }) => {
    await auth.register(newUser.email, newUser.password);
    await auth.expectUserAuthorized();
  });

  test.describe("Validation", () => {
    test("Email validation", async () => {
      await auth.registerAndExpectEmailValidationFailure(
        "invalid-email",
        newUser.password,
        "Please enter a valid email address",
      );
    });

    test.describe("Password validation", () => {
      test("Password validation (no letter)", async () => {
        await auth.openRegisterModal();
        await auth.registerModal.fillForm(newUser.email, "12345678");
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          "Password must contain at least one letter",
        );
      });
      test("Password validation (less than 8 characters)", async () => {
        await auth.openRegisterModal();
        await auth.registerModal.fillForm(newUser.email, "Short1!");
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          "Password must be at least 8 characters long",
        );
      });
      test("Password validation (no number)", async () => {
        await auth.openRegisterModal();
        await auth.registerModal.fillForm(
          newUser.email,
          "passwordWithoutNumbers",
        );
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          "Password must contain at least one number",
        );
      });
    });
  });
});
