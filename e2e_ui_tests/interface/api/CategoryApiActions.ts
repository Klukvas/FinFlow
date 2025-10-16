import { CategoryApiClient, CategoryFilters } from "../../infra/api/CategoryApiClient";
import { CategoryData } from "../../types";
import { Category } from "../../types/api";

export class CategoryApiActions {
  private categoryApiClient: CategoryApiClient;

  constructor(categoryApiClient: CategoryApiClient) {
    this.categoryApiClient = categoryApiClient;
  }

  async createMultipleCategories(token: string, categories: CategoryData[]): Promise<{ created: number; errors: string[] }> {
    let created = 0;
    this.categoryApiClient.setToken(token);
    const errors: string[] = [];

    for (const category of categories) {
      try {
        await this.categoryApiClient.createCategory({
          name: category.name,
          type: category.type as 'EXPENSE' | 'INCOME',
          parent_id: category.parentCategoryName ? parseInt(category.parentCategoryName) : undefined
        });
        created++;
      } catch (error: any) {
        errors.push(`Failed to create category "${category.name}": ${error.message}`);
      }
    }

    return { created, errors };
  }


  async deleteCategory(id: number): Promise<void> {
    const response = await this.categoryApiClient.deleteCategory(id);
    
    if (response.error) {
      throw new Error(`Failed to delete category: ${response.error}`);
    }
    
  }

  async deleteAllCategories(token: string): Promise<number> {
    this.categoryApiClient.setToken(token);

    // Get all categories (flat list to avoid hierarchy issues)
    const categoriesResponse = await this.categoryApiClient.getAllCategoriesFlat();
    
    if (categoriesResponse.error) {
      throw new Error(`Failed to fetch categories: ${categoriesResponse.error}`);
    }
    if (!categoriesResponse.data) {
      return 0;
    }

    const categories = categoriesResponse.data;
    
    let deletedCount = 0;
    const errors: string[] = [];

    // Delete categories in reverse order (children first, then parents)
    // Sort by ID descending to delete children before parents
    const sortedCategories = categories.sort((a, b) => b.id - a.id);

    for (const category of sortedCategories) {
      try {
        await this.deleteCategory(category.id);
        deletedCount++;
      } catch (error: any) {
        const errorMsg = `Failed to delete category ${category.id} (${category.name}): ${error.message}`;
        errors.push(errorMsg);
      }
    }


    if (errors.length > 0 && deletedCount === 0) {
      // If no categories were deleted and there were errors, throw an error
      const errorMsg = `Failed to delete any categories. Errors: ${errors.join('; ')}`;
      throw new Error(errorMsg);
    } else if (errors.length > 0) {
      // If some categories were deleted but there were errors, log warnings
    }

    return deletedCount;
  }
}