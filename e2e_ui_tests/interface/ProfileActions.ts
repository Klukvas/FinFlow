import { expect, Page } from "@playwright/test";
import { ProfilePage } from "../infra/pages/ProfilePage";

export class ProfileActions {
  private profilePage: ProfilePage;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.profilePage = new ProfilePage(page);
  }

  // Page expectations
  async expectPageVisible(): Promise<void> {
    await this.profilePage.expectPageVisible();
  }

  async expectUserInfoVisible(): Promise<void> {
    await this.profilePage.expectUserInfoVisible();
  }

  // Verify user email is displayed
  async expectEmailDisplayed(email: string): Promise<void> {
    await expect(this.profilePage.email).toBeVisible();
    await expect(this.profilePage.email).toContainText(email);
  }

  // Verify user heading contains email
  async expectUserHeadingContains(text: string): Promise<void> {
    await expect(this.profilePage.userHeading).toBeVisible();
    await expect(this.profilePage.userHeading).toContainText(text);
  }

  // Verify subscription section is visible
  async expectSubscriptionVisible(): Promise<void> {
    await this.profilePage.expectSubscriptionVisible();
  }

  // Verify plan code is displayed
  async expectPlanCodeVisible(): Promise<void> {
    await expect(this.profilePage.planCode).toBeVisible();
  }

  // Verify subscription status badge
  async expectSubscriptionStatusVisible(): Promise<void> {
    await expect(this.profilePage.subscriptionStatus).toBeVisible();
  }

  // Verify subscription status text
  async expectSubscriptionStatus(status: string): Promise<void> {
    await expect(this.profilePage.subscriptionStatus).toContainText(status, {
      ignoreCase: true,
    });
  }

  // Verify plan code text
  async expectPlanCode(planCode: string): Promise<void> {
    await expect(this.profilePage.planCode).toContainText(planCode, {
      ignoreCase: true,
    });
  }
}
