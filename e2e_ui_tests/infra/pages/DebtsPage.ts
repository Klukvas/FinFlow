import { Page, Locator } from "@playwright/test";
import { BasePage } from "../BasePage";

export class DebtsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Header
  get addDebtButton() {
    return this.page.locator("button").filter({ hasText: /add|create/i }).first();
  }

  // Tabs
  get debtsTab() {
    return this.page.locator('[role="tab"], button').filter({ hasText: /debts/i }).first();
  }

  get contactsTab() {
    return this.page.locator('[role="tab"], button').filter({ hasText: /contacts/i }).first();
  }

  // KPI strip cards
  get summaryStrip() {
    return this.page.locator(".grid").filter({ hasText: /outstanding|paid|active|interest/i }).first();
  }

  // Debt table (desktop)
  get debtTable() {
    return this.page.locator("table").first();
  }

  get debtTableRows() {
    return this.debtTable.locator("tbody tr");
  }

  // Contact table
  get contactTable() {
    return this.page.locator("table").first();
  }

  // Side panel
  get sidePanel() {
    return this.page.locator(".fixed.inset-y-0.right-0").first();
  }

  get sidePanelCloseButton() {
    return this.sidePanel.locator("button").filter({ hasText: "" }).locator("svg").first();
  }

  // Helper to get a debt row by name in the table
  getDebtRowByName(name: string): Locator {
    return this.debtTable.locator("tbody tr").filter({ hasText: name }).first();
  }

  // Helper to get a contact row by name
  getContactRowByName(name: string): Locator {
    return this.contactTable.locator("tbody tr").filter({ hasText: name }).first();
  }

  // Get the make-payment button on a debt row
  getDebtMakePaymentButton(debtRow: Locator): Locator {
    // The payment button is the first action button (the + icon)
    return debtRow.locator("button").first();
  }

  // Get the edit button on a debt row
  getDebtEditButton(debtRow: Locator): Locator {
    return debtRow.locator('button[title*="dit"], button[title*="Edit"]').first();
  }

  // Get the delete button on a debt row
  getDebtDeleteButton(debtRow: Locator): Locator {
    return debtRow.locator('button[title*="elete"], button[title*="Delete"]').first();
  }

  // Get the edit button on a contact row
  getContactEditButton(contactRow: Locator): Locator {
    return contactRow.locator("button").first();
  }

  // Get the delete button on a contact row
  getContactDeleteButton(contactRow: Locator): Locator {
    return contactRow.locator("button").nth(1);
  }
}
