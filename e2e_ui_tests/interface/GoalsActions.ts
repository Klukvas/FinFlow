import { expect, Page } from "@playwright/test";
import { GoalsPage } from "../infra/pages/GoalsPage";
import { GoalFormModal } from "../infra/modals/GoalFormModal";
import { GoalProgressModal } from "../infra/modals/GoalProgressModal";

export interface GoalData {
  title: string;
  description?: string;
  goalType?: string;
  priority?: string;
  targetAmount: string;
}

export class GoalsActions {
  private goalsPage: GoalsPage;
  private goalFormModal: GoalFormModal;
  private goalProgressModal: GoalProgressModal;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.goalsPage = new GoalsPage(page);
    this.goalFormModal = new GoalFormModal(page);
    this.goalProgressModal = new GoalProgressModal(page);
  }

  // Page expectations
  async expectPageVisible(): Promise<void> {
    await this.goalsPage.expectPageVisible();
  }

  async expectGoalTableVisible(): Promise<void> {
    await this.goalsPage.expectGoalTableVisible();
  }

  async expectSummaryStripVisible(): Promise<void> {
    await this.goalsPage.expectSummaryStripVisible();
  }

  // Create goal
  async createGoal(data: GoalData): Promise<void> {
    await this.openCreateGoalModal();
    await this.goalFormModal.fillForm({
      title: data.title,
      description: data.description,
      goalType: data.goalType,
      priority: data.priority,
      targetAmount: data.targetAmount,
    });
    await this.goalFormModal.submitButton.click();
    await this.expectCreateModalHidden();
  }

  async openCreateGoalModal(): Promise<void> {
    await this.goalsPage.createGoalButton.click();
    await this.goalFormModal.expectModal();
  }

  async expectCreateModalHidden(): Promise<void> {
    await expect(this.goalFormModal.modal).toBeHidden({ timeout: 10000 });
  }

  // Verify goal created (appears in the table)
  async expectGoalVisible(title: string): Promise<void> {
    await this.goalsPage.expectGoalRowVisible(title);
  }

  async expectGoalHidden(title: string): Promise<void> {
    await this.goalsPage.expectGoalRowHidden(title);
  }

  // Update progress
  async updateGoalProgress(title: string, amount: string): Promise<void> {
    const goalRow = this.goalsPage.getGoalRowByTitle(title);
    const updateButton = goalRow.locator(
      '[data-testid^="goal-update-progress-"]',
    );
    await updateButton.click();
    await this.goalProgressModal.expectModal();
    await this.goalProgressModal.fillAmount(amount);
    await this.goalProgressModal.submitButton.click();
    await expect(this.goalProgressModal.modal).toBeHidden({ timeout: 10000 });
  }

  // Edit goal
  async editGoal(
    title: string,
    updatedData: Partial<GoalData>,
  ): Promise<void> {
    const goalRow = this.goalsPage.getGoalRowByTitle(title);
    const editButton = goalRow.locator('[data-testid^="goal-edit-"]');
    await editButton.click();
    await this.goalFormModal.expectModal();
    await this.goalFormModal.fillForm({
      title: updatedData.title,
      description: updatedData.description,
      goalType: updatedData.goalType,
      priority: updatedData.priority,
      targetAmount: updatedData.targetAmount,
    });
    await this.goalFormModal.submitButton.click();
    await this.expectCreateModalHidden();
  }

  // Delete goal
  async deleteGoal(title: string): Promise<void> {
    const goalRow = this.goalsPage.getGoalRowByTitle(title);
    const deleteButton = goalRow.locator('[data-testid^="goal-delete-"]');
    await deleteButton.click();

    // Confirm deletion
    const confirmButton = this.goalsPage.confirmDeleteButton;
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();
    await expect(confirmButton).toBeHidden({ timeout: 10000 });
    // Wait for data refresh
    await this.page.waitForTimeout(2000);
  }

  // Check goal progress percentage
  async expectGoalProgressPercentage(
    title: string,
    expectedPercentage: string,
  ): Promise<void> {
    const goalRow = this.goalsPage.getGoalRowByTitle(title);
    await expect(goalRow).toContainText(expectedPercentage);
  }

  // Check goal status badge
  async expectGoalHasStatus(title: string, status: string): Promise<void> {
    const goalRow = this.goalsPage.getGoalRowByTitle(title);
    await expect(goalRow).toContainText(status);
  }
}
