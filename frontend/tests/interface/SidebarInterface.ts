import { Page } from '@playwright/test';
import { SidebarComponent } from '../infra/components/SidebarComponent';

export class SidebarInterface {
  private page: Page;
  private sidebarComponent: SidebarComponent;

  constructor(page: Page) {
    this.page = page;
    this.sidebarComponent = new SidebarComponent(page);
  }

  // Direct access to sidebar component
  get component() { return this.sidebarComponent; }

  /**
   * Business workflow: Navigate to category page
   */
  async navigateToCategory(): Promise<void> {
    await this.sidebarComponent.categoryLink.click();
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForURL('category');
  }

  /**
   * Business workflow: Navigate to expense page
   */
  async navigateToExpense(): Promise<void> {
    await this.sidebarComponent.expenseLink.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Navigate to income page
   */
  async navigateToIncome(): Promise<void> {
    await this.sidebarComponent.incomeLink.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Navigate to account page
   */
  async navigateToAccount(): Promise<void> {
    await this.sidebarComponent.accountLink.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Navigate to goals page
   */
  async navigateToGoals(): Promise<void> {
    await this.sidebarComponent.goalsLink.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Navigate to profile page
   */
  async navigateToProfile(): Promise<void> {
    await this.sidebarComponent.profileLink.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Navigate to specific page
   */
  async navigateTo(page: 'category' | 'expense' | 'income' | 'account' | 'goals' | 'profile'): Promise<void> {
    switch (page) {
      case 'category':
        await this.navigateToCategory();
        break;
      case 'expense':
        await this.navigateToExpense();
        break;
      case 'income':
        await this.navigateToIncome();
        break;
      case 'account':
        await this.navigateToAccount();
        break;
      case 'goals':
        await this.navigateToGoals();
        break;
      case 'profile':
        await this.navigateToProfile();
        break;
    }
  }

  /**
   * Business workflow: Toggle sidebar visibility
   */
  async toggleSidebar(): Promise<void> {
    await this.sidebarComponent.sidebarToggle.click();
  }

  /**
   * Business workflow: Close sidebar
   */
  async closeSidebar(): Promise<void> {
    await this.sidebarComponent.sidebarClose.click();
  }

  /**
   * Business workflow: Perform logout
   */
  async performLogout(): Promise<void> {
    await this.sidebarComponent.logoutButton.click();
    await this.sidebarComponent.logoutConfirmButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Business workflow: Click user profile
   */
  async clickUserProfile(): Promise<void> {
    await this.sidebarComponent.userProfileButton.click();
  }

  /**
   * Business workflow: Verify user is logged in (sidebar fully functional)
   */
  async expectUserLoggedIn(): Promise<void> {
    await this.sidebarComponent.expectComponent();
    await this.sidebarComponent.expectUserSectionVisible();
  }

  /**
   * Business workflow: Verify user is logged out (sidebar hidden)
   */
  async expectUserLoggedOut(): Promise<void> {
    // When logged out, the sidebar should not be visible or functional
    // This is a placeholder - implement based on your app's behavior
  }

  /**
   * Business workflow: Verify sidebar is visible and functional
   */
  async expectSidebarVisible(): Promise<void> {
    await this.sidebarComponent.expectComponent();
  }

  /**
   * Business workflow: Verify sidebar is hidden
   */
  async expectSidebarHidden(): Promise<void> {
    // This would need to be implemented based on your app's behavior
    // when sidebar is hidden
  }

  /**
   * Business workflow: Verify all navigation links are visible
   */
  async expectAllNavigationLinksVisible(): Promise<void> {
    await this.sidebarComponent.expectComponent();
  }

  /**
   * Business workflow: Verify user section is visible
   */
  async expectUserSectionVisible(): Promise<void> {
    await this.sidebarComponent.expectUserSectionVisible();
  }

  /**
   * Business workflow: Verify user profile button is visible
   */
  async expectUserProfileButtonVisible(): Promise<void> {
    await this.sidebarComponent.expectUserSectionVisible();
  }

  /**
   * Business workflow: Verify user profile button is hidden
   */
  async expectUserProfileButtonHidden(): Promise<void> {
    // This would need to be implemented based on your app's behavior
  }

  /**
   * Business workflow: Verify logout button is visible
   */
  async expectLogoutButtonVisible(): Promise<void> {
    // This would need to be implemented based on your app's behavior
  }

  /**
   * Business workflow: Verify logout button is hidden
   */
  async expectLogoutButtonHidden(): Promise<void> {
    // This would need to be implemented based on your app's behavior
  }
}
