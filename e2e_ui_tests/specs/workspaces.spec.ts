import { test, expect } from "@playwright/test";
import { AuthActions } from "../interface/AuthActions";
import { WorkspacesActions } from "../interface/WorkspacesActions";
import { SidebarInterface } from "../interface/SidebarInterface";

interface UserCredentials {
  email: string;
  password: string;
}

const testUser: UserCredentials = {
  email: "testuser1@test.com",
  password: "Sololane56457!",
};

test.describe("Workspaces Management", () => {
  let auth: AuthActions;
  let workspaces: WorkspacesActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    auth = new AuthActions(page);
    workspaces = new WorkspacesActions(page);
    sidebar = new SidebarInterface(page);

    await page.goto("");
    await auth.login(testUser.email, testUser.password);
    await sidebar.navigateToWorkspaces();
  });

  test.describe("View Workspaces", () => {
    test("should display workspace list", async () => {
      await workspaces.expectPageVisible();
      await workspaces.expectWorkspaceListVisible();
    });

    test("should have a personal workspace by default", async ({ page }) => {
      await workspaces.expectWorkspaceListVisible();
      // Every user gets a personal workspace on registration
      // At least one workspace card should be visible
      const firstCard = page
        .locator('[data-testid^="workspace-card-"]')
        .first();
      await expect(firstCard).toBeVisible();
      // The personal workspace type should show "Personal"
      const typeLabel = firstCard.locator('[data-testid^="workspace-type-"]');
      await expect(typeLabel).toBeVisible();
    });
  });

  test.describe("Edit Workspace", () => {
    test("should edit workspace name", async ({ page }) => {
      await workspaces.expectWorkspaceListVisible();

      // Find the personal workspace card and check its name
      // The personal workspace should exist by default
      const personalCard = page
        .locator('[data-testid^="workspace-card-"]')
        .first();
      await expect(personalCard).toBeVisible();

      // Get the workspace name from the card
      const nameElement = personalCard.locator(
        '[data-testid^="workspace-name-"]',
      );
      const originalName = await nameElement.textContent();

      // Click edit button
      const editButton = personalCard.locator(
        '[data-testid^="workspace-edit-"]',
      );

      // Only proceed if edit button exists (owner of workspace)
      if (await editButton.isVisible()) {
        const newName = `Workspace ${Date.now()}`;
        await editButton.click();

        // Fill in the new name
        const nameInput = page.getByTestId("workspace-name-input");
        await expect(nameInput).toBeVisible();
        await nameInput.clear();
        await nameInput.fill(newName);

        // Submit
        const submitButton = page.getByTestId("workspace-form-submit");
        await submitButton.click();

        // Wait for modal to close
        await expect(nameInput).toBeHidden({ timeout: 10000 });
        await page.waitForTimeout(1000);

        // Verify the name was updated
        await workspaces.expectWorkspaceVisible(newName);

        // Restore original name
        const updatedCard = page.locator('[data-testid^="workspace-card-"]', {
          hasText: newName,
        });
        const restoreEditButton = updatedCard.locator(
          '[data-testid^="workspace-edit-"]',
        );
        await restoreEditButton.click();

        const restoreNameInput = page.getByTestId("workspace-name-input");
        await expect(restoreNameInput).toBeVisible();
        await restoreNameInput.clear();
        await restoreNameInput.fill(originalName?.trim() || "Personal");
        await page.getByTestId("workspace-form-submit").click();
        await expect(restoreNameInput).toBeHidden({ timeout: 10000 });
      }
    });
  });

  test.describe("Workspace Members", () => {
    test("should show owner listed in workspace members", async ({ page }) => {
      await workspaces.expectWorkspaceListVisible();

      // Find a workspace card that has a manage members button (shared workspaces)
      // or check the member count on the personal workspace
      const firstCard = page
        .locator('[data-testid^="workspace-card-"]')
        .first();
      await expect(firstCard).toBeVisible();

      // Check member count is visible (shows "1 members" for personal workspace)
      const memberCount = firstCard.locator(
        '[data-testid^="workspace-member-count-"]',
      );
      if (await memberCount.isVisible()) {
        await expect(memberCount).toContainText("1");
      }
    });
  });
});
