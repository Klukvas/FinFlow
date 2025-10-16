import { Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class SidebarComponent extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Element selectors using data-testid
  get sidebar() { return this.getByTestId('sidebar'); }
  get sidebarToggle() { return this.getByTestId('sidebar-toggle'); }
  get sidebarClose() { return this.getByTestId('sidebar-close'); }
  
  // Navigation links
  get categoryLink() { return this.getByTestId('sidebar-category-link'); }
  get expenseLink() { return this.getByTestId('sidebar-expense-link'); }
  get incomeLink() { return this.getByTestId('sidebar-income-link'); }
  get accountLink() { return this.getByTestId('sidebar-account-link'); }
  get goalsLink() { return this.getByTestId('sidebar-goals-link'); }
  get profileLink() { return this.getByTestId('sidebar-profile-link'); }
  
  // User profile section
  get userProfileButton() { return this.getByTestId('user-profile-button-sidebar'); }
  get userAvatar() { return this.getByTestId('user-avatar'); }
  get userName() { return this.getByTestId('user-name'); }
  get userEmail() { return this.getByTestId('user-email'); }
  
  // Logout section
  get logoutButton() { return this.getByTestId('logout-button'); }
  get logoutConfirmButton() { return this.getByTestId('logout-confirm-button'); }

  async expectComponent(): Promise<void> {
    await expect(this.categoryLink).toBeVisible();
    await expect(this.expenseLink).toBeVisible();
    await expect(this.incomeLink).toBeVisible();
    await expect(this.accountLink).toBeVisible();
    await expect(this.goalsLink).toBeVisible();
    await expect(this.profileLink).toBeVisible();
  }

  async expectUserSectionVisible(): Promise<void> {
    await expect(this.userProfileButton).toBeVisible();
    await expect(this.userName).toBeVisible();
    await expect(this.userEmail).toBeVisible();
  }
}
