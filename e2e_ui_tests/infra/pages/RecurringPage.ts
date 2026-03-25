import { Page, Locator } from "@playwright/test";
import { BasePage } from "../BasePage";

export class RecurringPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Header
  get addButton() {
    return this.page.locator("button").filter({ hasText: /add|create/i }).first();
  }

  // KPI strip
  get summaryStrip() {
    return this.page.locator(".grid").first();
  }

  // Upcoming executions section
  get upcomingSection() {
    return this.page.locator("h3").filter({ hasText: /upcoming/i }).first();
  }

  // Table (desktop)
  get table() {
    return this.page.locator("table").first();
  }

  get tableRows() {
    return this.table.locator("tbody tr");
  }

  // Side panel
  get sidePanel() {
    return this.page.locator(".fixed.inset-y-0.right-0").first();
  }

  // Get a recurring payment row by name
  getPaymentRowByName(name: string): Locator {
    return this.table.locator("tbody tr").filter({ hasText: name }).first();
  }

  // Get the pause/resume button on a row
  getPaymentPauseResumeButton(row: Locator): Locator {
    // The pause/resume button is the first action button in the actions cell
    return row.locator("td:last-child button").first();
  }

  // Get the edit button on a row
  getPaymentEditButton(row: Locator): Locator {
    return row.locator('button[title*="dit"], button[title*="Edit"]').first();
  }

  // Get the delete button on a row
  getPaymentDeleteButton(row: Locator): Locator {
    return row.locator('button[title*="elete"], button[title*="Delete"]').first();
  }
}
