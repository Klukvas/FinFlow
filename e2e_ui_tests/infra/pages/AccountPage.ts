import { Page, Locator } from "@playwright/test";
import { BasePage } from "../BasePage";

export class AccountPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page container
  get accountPage() {
    return this.getByTestId("account-page");
  }

  // Header
  get pageHeader() {
    return this.getByTestId("account-page-header");
  }

  get createAccountButton() {
    return this.getByTestId("create-account-button");
  }

  // Summary strip
  get summaryStrip() {
    return this.getByTestId("account-summary-strip");
  }

  // Table
  get accountTable() {
    return this.getByTestId("account-table");
  }

  // Get specific account row by ID
  getAccountRow(accountId: number): Locator {
    return this.getByTestId(`account-row-${accountId}`);
  }

  // Get account row by name (searches table for text)
  getAccountRowByName(name: string): Locator {
    return this.page
      .getByTestId("account-table")
      .locator("tr")
      .filter({ hasText: name });
  }

  // Get edit button within an account row
  getEditButton(row: Locator): Locator {
    return row.getByTestId("account-edit-button");
  }

  // Get archive button within an account row
  getArchiveButton(row: Locator): Locator {
    return row.getByTestId("account-archive-button");
  }

  // Archive confirmation
  get confirmArchiveButton() {
    return this.getByTestId("confirm-archive-button");
  }
}
