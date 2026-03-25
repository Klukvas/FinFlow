import { expect, Page } from "@playwright/test";
import { AccountPage } from "../infra/pages/AccountPage";
import {
  CreateAccountModal,
  AccountFormData,
} from "../infra/modals/CreateAccountModal";
import { EditAccountModal } from "../infra/modals/EditAccountModal";

export class AccountActions {
  private accountPage: AccountPage;
  private createModal: CreateAccountModal;
  private editModal: EditAccountModal;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.accountPage = new AccountPage(page);
    this.createModal = new CreateAccountModal(page);
    this.editModal = new EditAccountModal(page);
  }

  // Page visibility
  async expectPageVisible(): Promise<void> {
    await expect(this.accountPage.accountPage).toBeVisible();
  }

  async expectPageHeaderVisible(): Promise<void> {
    await expect(this.accountPage.pageHeader).toBeVisible();
  }

  async expectSummaryStripVisible(): Promise<void> {
    await expect(this.accountPage.summaryStrip).toBeVisible();
  }

  async expectTableVisible(): Promise<void> {
    await expect(this.accountPage.accountTable).toBeVisible();
  }

  // Create account flow
  async openCreateModal(): Promise<void> {
    await this.accountPage.createAccountButton.click();
    await this.createModal.expectModal();
  }

  async createAccount(data: AccountFormData): Promise<void> {
    await this.openCreateModal();
    await this.createModal.fillForm(data);
    await this.createModal.submitButton.click();
    // Wait for modal to close (account created)
    await expect(this.createModal.modal).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
  }

  async expectAccountInTable(accountName: string): Promise<void> {
    const row = this.accountPage.getAccountRowByName(accountName);
    await expect(row).toBeVisible({ timeout: 10000 });
  }

  async expectAccountNotInTable(accountName: string): Promise<void> {
    const row = this.accountPage.getAccountRowByName(accountName);
    await expect(row).toBeHidden({ timeout: 10000 });
  }

  // Edit account flow
  async openEditModal(accountName: string): Promise<void> {
    const row = this.accountPage.getAccountRowByName(accountName);
    await expect(row).toBeVisible();
    const editButton = this.accountPage.getEditButton(row);
    await editButton.click();
    await this.editModal.expectModal();
  }

  async editAccount(
    accountName: string,
    updatedData: Partial<AccountFormData>,
  ): Promise<void> {
    await this.openEditModal(accountName);
    await this.editModal.fillForm(updatedData);
    await this.editModal.submitButton.click();
    // Wait for modal to close (account updated)
    await expect(this.editModal.modal).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
  }

  // Archive account flow
  async archiveAccount(accountName: string): Promise<void> {
    const row = this.accountPage.getAccountRowByName(accountName);
    await expect(row).toBeVisible();
    const archiveButton = this.accountPage.getArchiveButton(row);
    await archiveButton.click();
    // Confirm in the archive confirmation modal
    const confirmButton = this.accountPage.confirmArchiveButton;
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();
    await expect(confirmButton).toBeHidden({ timeout: 10000 });
    await this.page.waitForLoadState("networkidle");
    // Wait for the UI to update
    await this.page.waitForTimeout(1000);
  }
}
