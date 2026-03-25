import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { ProfileActions } from "../interface/ProfileActions";
import { SidebarInterface } from "../interface/SidebarInterface";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

test.describe("Profile Page", () => {
  let auth: AuthActions;
  let profile: ProfileActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    profile = new ProfileActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToProfile();
  });

  test.describe("View Profile", () => {
    test("should display profile page with user info", async () => {
      await profile.expectPageVisible();
      await profile.expectUserInfoVisible();
    });

    test("should display user email", async () => {
      await profile.expectEmailDisplayed(testUser.email);
    });

    test("should display user email in heading", async () => {
      await profile.expectUserHeadingContains(testUser.email);
    });
  });

  test.describe("Subscription", () => {
    test("should display subscription section", async () => {
      await profile.expectSubscriptionVisible();
    });

    test("should display subscription plan badge", async ({ page }) => {
      // Wait for subscription data to load
      await page.waitForLoadState("networkidle");
      // The subscription section should be visible with plan details
      await profile.expectSubscriptionVisible();
      // Plan code badge should be visible once subscription data loads
      await profile.expectPlanCodeVisible();
      await profile.expectSubscriptionStatusVisible();
    });
  });
});
