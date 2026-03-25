import { expect, Page } from "@playwright/test";
import { WorkspacesPage } from "../infra/pages/WorkspacesPage";

export class WorkspacesActions {
  private workspacesPage: WorkspacesPage;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.workspacesPage = new WorkspacesPage(page);
  }

  // Page expectations
  async expectPageVisible(): Promise<void> {
    await this.workspacesPage.expectPageVisible();
  }

  async expectWorkspaceListVisible(): Promise<void> {
    await this.workspacesPage.expectWorkspaceListVisible();
  }

  // Verify workspace exists by name
  async expectWorkspaceVisible(name: string): Promise<void> {
    await this.workspacesPage.expectWorkspaceVisible(name);
  }

  // Verify workspace type
  async expectWorkspaceType(
    name: string,
    expectedType: string,
  ): Promise<void> {
    const card = this.workspacesPage.getWorkspaceCardByName(name);
    const typeElement = card.locator('[data-testid^="workspace-type-"]');
    await expect(typeElement).toContainText(expectedType, { ignoreCase: true });
  }

  // Edit workspace name
  async editWorkspaceName(
    currentName: string,
    newName: string,
  ): Promise<void> {
    const card = this.workspacesPage.getWorkspaceCardByName(currentName);
    const editButton = card.locator('[data-testid^="workspace-edit-"]');
    await editButton.click();

    // Wait for the edit modal to appear
    const nameInput = this.workspacesPage.workspaceNameInput;
    await expect(nameInput).toBeVisible();

    await nameInput.clear();
    await nameInput.fill(newName);

    const submitButton = this.workspacesPage.workspaceFormSubmit;
    await submitButton.click();

    // Wait for the modal to close
    await expect(nameInput).toBeHidden({ timeout: 10000 });
  }

  // Get workspace member count text
  async expectWorkspaceMemberCount(
    name: string,
    expectedText: string,
  ): Promise<void> {
    const card = this.workspacesPage.getWorkspaceCardByName(name);
    const memberCount = card.locator(
      '[data-testid^="workspace-member-count-"]',
    );
    await expect(memberCount).toContainText(expectedText);
  }

  // Open workspace members modal
  async openMembersModal(name: string): Promise<void> {
    const card = this.workspacesPage.getWorkspaceCardByName(name);
    const manageMembersButton = card.locator(
      '[data-testid^="workspace-manage-members-"]',
    );
    await manageMembersButton.click();
    // Wait for the members modal to appear
    await this.page.waitForLoadState("networkidle");
  }

  // Verify a member card is visible
  async expectMemberVisible(userId: number): Promise<void> {
    const memberCard = this.workspacesPage.getMemberCard(userId);
    await expect(memberCard).toBeVisible();
  }

  // Verify member email
  async expectMemberEmail(userId: number, email: string): Promise<void> {
    const memberEmail = this.workspacesPage.getMemberEmail(userId);
    await expect(memberEmail).toContainText(email);
  }
}
