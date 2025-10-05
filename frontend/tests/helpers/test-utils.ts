import { Page, expect } from '@playwright/test';

/**
 * Utility functions for tests
 */
export class TestUtils {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingComplete(): Promise<void> {
    // Wait for any loading spinners to disappear
    const loadingSelectors = [
      '[data-testid*="loading"]',
      '[data-testid*="spinner"]',
      '.animate-spin'
    ];
    
    for (const selector of loadingSelectors) {
      try {
        await this.page.locator(selector).waitFor({ state: 'hidden', timeout: 5000 });
      } catch {
        // Ignore if loading element doesn't exist
      }
    }
  }

  /**
   * Take screenshot with timestamp
   */
  async takeScreenshot(name: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await this.page.screenshot({ 
      path: `screenshots/${name}-${timestamp}.png`, 
      fullPage: true 
    });
  }

  /**
   * Wait for element to be visible with custom timeout
   */
  async waitForElement(testId: string, timeout = 10000): Promise<void> {
    await this.page.getByTestId(testId).waitFor({ state: 'visible', timeout });
  }

  /**
   * Wait for element to be hidden with custom timeout
   */
  async waitForElementHidden(testId: string, timeout = 10000): Promise<void> {
    await this.page.getByTestId(testId).waitFor({ state: 'hidden', timeout });
  }

  /**
   * Check if element exists
   */
  async elementExists(testId: string): Promise<boolean> {
    try {
      await this.page.getByTestId(testId).waitFor({ state: 'visible', timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Generate random string
   */
  generateRandomString(length = 8): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Generate random email
   */
  generateRandomEmail(): string {
    const timestamp = Date.now();
    return `test-${timestamp}@example.com`;
  }

  /**
   * Generate random username
   */
  generateRandomUsername(): string {
    const timestamp = Date.now();
    return `testuser${timestamp}`;
  }

  /**
   * Generate random category name
   */
  generateRandomCategoryName(): string {
    const timestamp = Date.now();
    return `Test Category ${timestamp}`;
  }

  /**
   * Generate random expense description
   */
  generateRandomExpenseDescription(): string {
    const timestamp = Date.now();
    return `Test Expense ${timestamp}`;
  }

  /**
   * Format date for input fields
   */
  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Get current date formatted for input
   */
  getCurrentDate(): string {
    return this.formatDate(new Date());
  }

  /**
   * Get date X days ago
   */
  getDateDaysAgo(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return this.formatDate(date);
  }

  /**
   * Get date X days in future
   */
  getDateDaysFromNow(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return this.formatDate(date);
  }

  /**
   * Wait for network requests to complete
   */
  async waitForNetworkIdle(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Clear all form fields
   */
  async clearFormFields(selectors: string[]): Promise<void> {
    for (const selector of selectors) {
      try {
        await this.page.locator(selector).clear();
      } catch {
        // Ignore if element doesn't exist
      }
    }
  }

  /**
   * Fill form fields with data
   */
  async fillFormFields(data: Record<string, string>): Promise<void> {
    for (const [selector, value] of Object.entries(data)) {
      try {
        await this.page.locator(selector).fill(value);
      } catch {
        // Ignore if element doesn't exist
      }
    }
  }

  /**
   * Check if URL contains specific path
   */
  urlContains(path: string): boolean {
    return this.page.url().includes(path);
  }

  /**
   * Get text content from element
   */
  async getTextContent(testId: string): Promise<string> {
    return await this.page.getByTestId(testId).textContent() || '';
  }

  /**
   * Get input value from element
   */
  async getInputValue(testId: string): Promise<string> {
    return await this.page.getByTestId(testId).inputValue();
  }

  /**
   * Check if element is enabled
   */
  async isElementEnabled(testId: string): Promise<boolean> {
    return await this.page.getByTestId(testId).isEnabled();
  }

  /**
   * Check if element is visible
   */
  async isElementVisible(testId: string): Promise<boolean> {
    return await this.page.getByTestId(testId).isVisible();
  }

  /**
   * Click element by test ID
   */
  async clickElement(testId: string): Promise<void> {
    await this.page.getByTestId(testId).click();
  }

  /**
   * Fill input by test ID
   */
  async fillInput(testId: string, value: string): Promise<void> {
    await this.page.getByTestId(testId).fill(value);
  }

  /**
   * Select option by test ID
   */
  async selectOption(testId: string, value: string): Promise<void> {
    await this.page.getByTestId(testId).selectOption(value);
  }

  /**
   * Handle modal dialogs
   */
  async handleModalDialog(action: 'accept' | 'dismiss'): Promise<void> {
    this.page.on('dialog', async dialog => {
      if (action === 'accept') {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }

  /**
   * Wait for download to start
   */
  async waitForDownload(): Promise<string> {
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    return download.suggestedFilename();
  }

  /**
   * Assert element is visible
   */
  async assertElementVisible(testId: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toBeVisible();
  }

  /**
   * Assert element is hidden
   */
  async assertElementHidden(testId: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toBeHidden();
  }

  /**
   * Assert element contains text
   */
  async assertElementContainsText(testId: string, text: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toContainText(text);
  }

  /**
   * Assert element has value
   */
  async assertElementHasValue(testId: string, value: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toHaveValue(value);
  }

  /**
   * Assert element is enabled
   */
  async assertElementEnabled(testId: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toBeEnabled();
  }

  /**
   * Assert element is disabled
   */
  async assertElementDisabled(testId: string): Promise<void> {
    await expect(this.page.getByTestId(testId)).toBeDisabled();
  }

  /**
   * Assert URL contains path
   */
  async assertUrlContains(path: string): Promise<void> {
    expect(this.page.url()).toContain(path);
  }

  /**
   * Assert URL equals path
   */
  async assertUrlEquals(path: string): Promise<void> {
    expect(this.page.url()).toBe(path);
  }
}

