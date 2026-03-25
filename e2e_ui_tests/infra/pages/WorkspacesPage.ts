import { Page, Locator, expect } from "@playwright/test";
import { BasePage } from "../BasePage";

export class WorkspacesPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Page header
  get pageTitle(): Locator {
    return this.getByTestId("workspace-page-title");
  }

  // Workspace list
  get workspaceList(): Locator {
    return this.getByTestId("workspace-list");
  }

  // Get a specific workspace card by id
  getWorkspaceCard(workspaceId: string): Locator {
    return this.getByTestId(`workspace-card-${workspaceId}`);
  }

  getWorkspaceName(workspaceId: string): Locator {
    return this.getByTestId(`workspace-name-${workspaceId}`);
  }

  getWorkspaceType(workspaceId: string): Locator {
    return this.getByTestId(`workspace-type-${workspaceId}`);
  }

  getWorkspaceMemberCount(workspaceId: string): Locator {
    return this.getByTestId(`workspace-member-count-${workspaceId}`);
  }

  getWorkspaceEditButton(workspaceId: string): Locator {
    return this.getByTestId(`workspace-edit-${workspaceId}`);
  }

  getWorkspaceManageMembersButton(workspaceId: string): Locator {
    return this.getByTestId(`workspace-manage-members-${workspaceId}`);
  }

  // Workspace form (in modal)
  get workspaceNameInput(): Locator {
    return this.getByTestId("workspace-name-input");
  }

  get workspaceFormSubmit(): Locator {
    return this.getByTestId("workspace-form-submit");
  }

  // Find workspace card by name text (when we don't know the ID)
  getWorkspaceCardByName(name: string): Locator {
    return this.page.locator('[data-testid^="workspace-card-"]', {
      hasText: name,
    });
  }

  // Member cards
  getMemberCard(userId: number): Locator {
    return this.getByTestId(`member-card-${userId}`);
  }

  getMemberEmail(userId: number): Locator {
    return this.getByTestId(`member-email-${userId}`);
  }

  async expectPageVisible(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
  }

  async expectWorkspaceListVisible(): Promise<void> {
    await expect(this.workspaceList).toBeVisible();
  }

  async expectWorkspaceVisible(name: string): Promise<void> {
    await expect(this.getWorkspaceCardByName(name)).toBeVisible();
  }
}
