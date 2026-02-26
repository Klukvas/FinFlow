import { expect, Page } from "@playwright/test";
import { CategoryPage } from "../infra/pages/CategoryPage";
import { CreateCategoryModal } from "../infra/modals/CreateCategoryModal";
import { CategoryData, CreateCategoryFailureData } from "../types";

export class CategoryActions {
  private categoryPage: CategoryPage;
  private createCategoryModal: CreateCategoryModal;
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.categoryPage = new CategoryPage(page);
    this.createCategoryModal = new CreateCategoryModal(page);
  }

  // Category Statistics Actions
  async expectStatisticsVisible({
    totalCategories,
    expenseCategories,
    incomeCategories,
    parentCategories,
    childCategories,
  }: {
    totalCategories?: number;
    expenseCategories?: number;
    incomeCategories?: number;
    parentCategories?: number;
    childCategories?: number;
  }) {
    await expect(
      this.categoryPage.getByTestId("total-categories-stat"),
    ).toBeVisible();
    await expect(
      this.categoryPage.getByTestId("expense-categories-stat"),
    ).toBeVisible();
    await expect(
      this.categoryPage.getByTestId("income-categories-stat"),
    ).toBeVisible();
    await expect(
      this.categoryPage.getByTestId("parent-categories-stat"),
    ).toBeVisible();
    await expect(
      this.categoryPage.getByTestId("child-categories-stat"),
    ).toBeVisible();
    if (totalCategories) {
      await expect(
        this.categoryPage.getByTestId("total-categories-stat-value"),
      ).toContainText(totalCategories.toString());
    }
    if (expenseCategories) {
      await expect(
        this.categoryPage.getByTestId("expense-categories-stat-value"),
      ).toContainText(expenseCategories.toString());
    }
    if (incomeCategories) {
      await expect(
        this.categoryPage.getByTestId("income-categories-stat-value"),
      ).toContainText(incomeCategories.toString());
    }
    if (parentCategories) {
      await expect(
        this.categoryPage.getByTestId("parent-categories-stat-value"),
      ).toContainText(parentCategories.toString());
    }
    if (childCategories) {
      await expect(
        this.categoryPage.getByTestId("child-categories-stat-value"),
      ).toContainText(childCategories.toString());
    }
  }

  // Create Category Actions

  async createCategory({ name, type, parentCategoryName }: CategoryData) {
    await this.openCreateCategoryModal();
    await this.createCategoryModal.fillForm({ name, type, parentCategoryName });
    await this.createCategoryModal.submitButton.click();
    await this.expectCreateModalState("hidden");
  }

  async createCategoryAndExpectFailure({
    name,
    type,
    parentCategoryName,
    toastErrorMessage,
    formErrorMessage,
    nameError,
  }: CreateCategoryFailureData) {
    await this.openCreateCategoryModal();
    await this.createCategoryModal.fillForm({ name, type, parentCategoryName });
    await this.createCategoryModal.submitButton.click();
    await this.expectCreateModalState("visible");
    if (toastErrorMessage) {
      await this.createCategoryModal.expectErrorToast(toastErrorMessage);
    }
    if (formErrorMessage) {
      await this.createCategoryModal.expectFormError(formErrorMessage);
    }
    if (nameError) {
      await this.createCategoryModal.expectNameError(nameError);
    }
  }

  async expectCategoryTypeSelectState(
    type: "EXPENSE" | "INCOME",
    state: "disabled" | "enabled",
  ) {
    const categoryType = this.createCategoryModal.categoryTypeSelect;
    state === "disabled"
      ? await expect(categoryType).toBeDisabled()
      : await expect(categoryType).toBeEnabled();
    await expect(categoryType).toHaveValue(type);
  }

  async openCreateCategoryModal() {
    await this.categoryPage.createCategoryButton.click();
    await this.createCategoryModal.expectModal();
  }

  async expandCategoryInTree(categoryName: string) {
    const parentRow = this.categoryPage.getCategoryItem(categoryName);
    await expect(parentRow).toBeVisible();
    // Wait for tree data to refresh — the expand button appears in the first
    // cell only when the category has children
    const firstCell = parentRow.locator("td").first();
    const expandButton = firstCell.locator("button");
    await expect(expandButton).toBeVisible({ timeout: 10000 });
    await expandButton.click();
  }

  async expectCategoryCreated(category: CategoryData) {
    // If the category has a parent, expand the parent tree node only if child is not visible
    if (category.parentCategoryName) {
      const childRow = this.categoryPage.getCategoryItem(category.name);
      if (!(await childRow.isVisible())) {
        await this.expandCategoryInTree(category.parentCategoryName);
      }
    }
    const createdCategory = this.categoryPage.getCategoryItem(category.name);
    await expect(createdCategory).toBeVisible();
    await expect(createdCategory.getByTestId("category-name")).toContainText(
      category.name,
    );
    await expect(createdCategory.getByTestId("category-type")).toContainText(
      category.type,
      { ignoreCase: true },
    );
    if (category.parentCategoryName) {
      await expect(
        createdCategory.getByTestId("category-parent-name"),
      ).toContainText(category.parentCategoryName);
    } else {
      await expect(
        createdCategory.getByTestId("category-parent-name"),
      ).toContainText("Root Category");
    }
    await expect(createdCategory.getByTestId("category-id")).not.toBeEmpty();
  }

  // Edit Category Actions

  async editCategory(categoryName: string, updatedData: Partial<CategoryData>) {
    await this.openEditCategoryModal(categoryName);
    await this.createCategoryModal.fillForm(updatedData);
    await this.createCategoryModal.submitButton.click();
    await this.expectCreateModalState("hidden");
  }

  async editCategoryAndExpectFailure({
    categoryName,
    updatedData,
    toastErrorMessage,
    formErrorMessage,
    nameError,
  }: {
    categoryName: string;
    updatedData: Partial<CategoryData>;
    toastErrorMessage?: string;
    formErrorMessage?: string;
    nameError?: string;
  }) {
    await this.openEditCategoryModal(categoryName);
    await this.createCategoryModal.fillForm(updatedData);
    await this.createCategoryModal.submitButton.click();
    await this.expectCreateModalState("visible");
    if (toastErrorMessage) {
      await this.createCategoryModal.expectErrorToast(toastErrorMessage);
    }
    if (formErrorMessage) {
      await this.createCategoryModal.expectFormError(formErrorMessage);
    }
    if (nameError) {
      await this.createCategoryModal.expectNameError(nameError);
    }
  }

  async expectCreateModalState(state?: "hidden" | "visible") {
    const exp = expect(this.createCategoryModal.modal);
    state === "hidden" ? await exp.toBeHidden() : await exp.toBeVisible();
  }

  async openEditCategoryModal(categoryName: string) {
    await this.categoryPage
      .getCategoryItem(categoryName)
      .getByTestId("category-edit-button")
      .click();
    await this.createCategoryModal.expectModal();
  }

  // Delete Category Actions

  async deleteCategory(categoryName: string) {
    const category = this.categoryPage.getCategoryItem(categoryName);
    await category.getByTestId("category-delete-button").click();
    // Confirm deletion in the confirmation modal
    const confirmButton = this.page.getByTestId("confirm-delete-button");
    await expect(confirmButton).toBeVisible();
    // Log all responses to debug refresh behavior
    const responses: string[] = [];
    this.page.on("response", (resp) => {
      responses.push(
        `${resp.request().method()} ${resp.status()} ${resp.url()}`,
      );
    });
    await confirmButton.click();
    await expect(confirmButton).toBeHidden({ timeout: 10000 });
    // Wait a bit for any follow-up requests
    await this.page.waitForTimeout(3000);
    console.log("All responses after delete confirm:", responses);
  }

  async deleteCategoryAndExpectFailure(
    categoryName: string,
    toastErrorMessage: string,
    formErrorMessage: string,
    nameError: string,
  ) {
    const category = this.categoryPage.getCategoryItem(categoryName);
    await category.getByTestId("category-delete-button").click();
    // Confirm deletion in the confirmation modal
    await this.page.getByTestId("confirm-delete-button").click();
    if (toastErrorMessage) {
      await this.createCategoryModal.expectErrorToast(toastErrorMessage);
    }
    if (formErrorMessage) {
      await this.createCategoryModal.expectFormError(formErrorMessage);
    }
  }

  async expectDeleteButtonDisabled(categoryName: string) {
    const categoryRow = this.categoryPage.getCategoryItem(categoryName);
    const deleteButton = categoryRow.getByTestId("category-delete-button");
    await expect(deleteButton).toBeDisabled();
  }

  async expectCategoryDeleted(categoryName: string) {
    await expect(this.categoryPage.getCategoryItem(categoryName)).toBeHidden();
  }
}
