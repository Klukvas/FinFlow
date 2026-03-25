import { Page, Locator, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class ProfilePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page header
  get pageTitle(): Locator {
    return this.getByTestId("profile-page-title");
  }

  // User info
  get userHeading(): Locator {
    return this.getByTestId("profile-user-heading");
  }

  get emailSection(): Locator {
    return this.getByTestId("profile-email-section");
  }

  get email(): Locator {
    return this.getByTestId("profile-email");
  }

  // Subscription
  get subscriptionSection(): Locator {
    return this.getByTestId("profile-subscription-section");
  }

  get planCode(): Locator {
    return this.getByTestId("profile-plan-code");
  }

  get subscriptionStatus(): Locator {
    return this.getByTestId("profile-subscription-status");
  }

  async expectPageVisible(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectUserInfoVisible(): Promise<void> {
    await expect(this.userHeading).toBeVisible();
    await expect(this.emailSection).toBeVisible();
  }

  async expectSubscriptionVisible(): Promise<void> {
    await expect(this.subscriptionSection).toBeVisible();
  }
}
