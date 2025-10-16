import { Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class HeaderPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Element selectors using data-testid
  get loginModalTrigger() { return this.getByTestId('login-modal-trigger'); }
  get registerModalTrigger() { return this.getByTestId('register-modal-trigger'); }
  get userProfileButton() { return this.getByTestId('user-profile-button'); }
  get logoutButton() { return this.getByTestId('logout-button'); }
  get sidebarToggle() { return this.getByTestId('sidebar-toggle'); }
  get sidebar() { return this.getByTestId('sidebar'); }

  // Element expectations using expect
  async expectLoginModalTriggerVisible(): Promise<void> {
    await expect(this.loginModalTrigger).toBeVisible();
  }

  async expectLoginModalTriggerHidden(): Promise<void> {
    await expect(this.loginModalTrigger).toBeHidden();
  }

  async expectUserProfileButtonVisible(): Promise<void> {
    await expect(this.userProfileButton).toBeVisible();
  }

  async expectUserProfileButtonHidden(): Promise<void> {
    await expect(this.userProfileButton).toBeHidden();
  }

  async expectSidebarVisible(): Promise<void> {
    await expect(this.sidebar).toBeVisible();
  }

  async expectSidebarHidden(): Promise<void> {
    await expect(this.sidebar).toBeHidden();
  }
}