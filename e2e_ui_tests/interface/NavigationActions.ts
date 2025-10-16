import { Page, expect } from '@playwright/test';

export class NavigationActions {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to specific page
   */
  async goto(page: 'category' | 'expense' | 'income' | 'account' | 'goals' | 'profile' | 'home'): Promise<void> {
    const routes = {
      home: '/',
      category: '/category',
      expense: '/expense',
      income: '/income',
      account: '/account',
      goals: '/goals',
      profile: '/profile'
    };
    
    try {
      await this.page.goto(routes[page], { 
        waitUntil: 'domcontentloaded',
        timeout: 10000 
      });
    } catch (error) {
      console.error(`Failed to navigate to ${routes[page]}:`, error);
      throw error;
    }
  }


  /**
   * Use header navigation
   */
  async navigateViaHeader(page: 'category' | 'expense' | 'income' | 'account' | 'goals' | 'profile'): Promise<void> {
    // TODO: Use HeaderPage when header navigation methods are added
    // await this.headerPage.navigateViaHeader(page);
    
    // Temporary implementation with direct locators - should be removed
    const headerSelectors = {
      category: 'header-category-link',
      expense: 'header-expense-link',
      income: 'header-income-link',
      account: 'header-account-link',
      goals: 'header-goals-link',
      profile: 'header-profile-link'
    };

    await this.page.getByTestId(headerSelectors[page]).click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get current page URL
   */
  getCurrentUrl(): string {
    return this.page.url();
  }

  /**
   * Check if currently on specific page
   */
  async isOnPage(page: 'category' | 'expense' | 'income' | 'account' | 'goals' | 'profile' | 'home'): Promise<boolean> {
    const currentUrl = this.getCurrentUrl();
    const expectedRoutes = {
      home: '/',
      category: '/category',
      expense: '/expense',
      income: '/income',
      account: '/account',
      goals: '/goals',
      profile: '/profile'
    };
    
    return currentUrl.includes(expectedRoutes[page]);
  }

  /**
   * Wait for page to load completely
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Reload current page
   */
  async reload(): Promise<void> {
    await this.page.reload();
    await this.waitForPageLoad();
  }

  /**
   * Go back in browser history
   */
  async goBack(): Promise<void> {
    await this.page.goBack();
    await this.waitForPageLoad();
  }

  /**
   * Go forward in browser history
   */
  async goForward(): Promise<void> {
    await this.page.goForward();
    await this.waitForPageLoad();
  }

  /**
   * Wait for navigation to complete
   */
  async waitForNavigation(): Promise<void> {
    await this.page.waitForURL('**');
  }

  /**
   * Check if user is redirected to login (not authenticated)
   */
  async isRedirectedToLogin(): Promise<boolean> {
    const currentUrl = this.getCurrentUrl();
    return currentUrl.includes('/') && !currentUrl.includes('/category');
  }

  /**
   * Check if user is on dashboard (authenticated)
   */
  async isOnDashboard(): Promise<boolean> {
    return await this.isOnPage('category');
  }


}

