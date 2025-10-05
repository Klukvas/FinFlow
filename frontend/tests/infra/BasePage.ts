import { Page, Locator } from '@playwright/test';

export abstract class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Get element by data-testid
   */
  getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }
}