import { Page, Locator, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class GoalsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page header
  get pageHeader(): Locator {
    return this.getByTestId("goal-page-header");
  }

  get pageTitle(): Locator {
    return this.getByTestId("goal-page-title");
  }

  get createGoalButton(): Locator {
    return this.getByTestId("create-goal-button");
  }

  // Summary strip
  get summaryStrip(): Locator {
    return this.getByTestId("goal-summary-strip");
  }

  getKpiCard(index: number): Locator {
    return this.getByTestId(`goal-kpi-${index}`);
  }

  // Goal table
  get goalTable(): Locator {
    return this.getByTestId("goal-table");
  }

  getGoalRow(goalId: number): Locator {
    return this.getByTestId(`goal-row-${goalId}`);
  }

  getGoalTitle(goalId: number): Locator {
    return this.getByTestId(`goal-title-${goalId}`);
  }

  getGoalUpdateProgressButton(goalId: number): Locator {
    return this.getByTestId(`goal-update-progress-${goalId}`);
  }

  getGoalEditButton(goalId: number): Locator {
    return this.getByTestId(`goal-edit-${goalId}`);
  }

  getGoalDeleteButton(goalId: number): Locator {
    return this.getByTestId(`goal-delete-${goalId}`);
  }

  // Delete confirmation
  get confirmDeleteButton(): Locator {
    return this.getByTestId("confirm-delete-goal-button");
  }

  // Find a goal row by title text (when we don't know the ID)
  getGoalRowByTitle(title: string): Locator {
    return this.page.locator('[data-testid^="goal-row-"]', {
      hasText: title,
    });
  }

  async expectPageVisible(): Promise<void> {
    await expect(this.pageHeader).toBeVisible();
    await expect(this.pageTitle).toBeVisible();
  }

  async expectGoalTableVisible(): Promise<void> {
    await expect(this.goalTable).toBeVisible();
  }

  async expectSummaryStripVisible(): Promise<void> {
    await expect(this.summaryStrip).toBeVisible();
  }

  async expectGoalRowVisible(title: string): Promise<void> {
    await expect(this.getGoalRowByTitle(title)).toBeVisible();
  }

  async expectGoalRowHidden(title: string): Promise<void> {
    await expect(this.getGoalRowByTitle(title)).toBeHidden();
  }
}
