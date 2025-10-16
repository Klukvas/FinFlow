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
    console.log(`🔧 deleteCategory: Attempting to delete category ID ${id}`);
    const response = await this.categoryApiClient.deleteCategory(id);
    console.log(`🔧 deleteCategory: Delete response for ID ${id}:`, response);
    
    if (response.error) {
      console.error(`❌ deleteCategory: Error deleting category ID ${id}:`, response.error);
      throw new Error(`Failed to delete category: ${response.error}`);
    }
    
    console.log(`✅ deleteCategory: Successfully deleted category ID ${id}`);
  }

  async deleteAllCategories(token: string): Promise<number> {
    console.log('🗑️ deleteAllCategories: Starting cleanup with token:', token ? 'Present' : 'Missing');
    this.categoryApiClient.setToken(token);

    // Get all categories (flat list to avoid hierarchy issues)
    console.log('📋 deleteAllCategories: Fetching all categories...');
    const categoriesResponse = await this.categoryApiClient.getAllCategoriesFlat();
    
    console.log('📋 deleteAllCategories: Categories response:', categoriesResponse);
    if (categoriesResponse.error) {
      console.error(`❌ deleteAllCategories: Error fetching categories:`, categoriesResponse.error);
      throw new Error(`Failed to fetch categories: ${categoriesResponse.error}`);
    }
    if (!categoriesResponse.data) {
      console.log('⚠️ deleteAllCategories: No categories found or error in response');
      return 0;
    }

    const categories = categoriesResponse.data;
    console.log(`📋 deleteAllCategories: Found ${categories.length} categories:`, categories.map(c => `${c.id}:${c.name}`));
    
    let deletedCount = 0;
    const errors: string[] = [];

    // Delete categories in reverse order (children first, then parents)
    // Sort by ID descending to delete children before parents
    const sortedCategories = categories.sort((a, b) => b.id - a.id);
    console.log(`🔄 deleteAllCategories: Sorted categories for deletion:`, sortedCategories.map(c => `${c.id}:${c.name}`));

    for (const category of sortedCategories) {
      try {
        console.log(`🗑️ deleteAllCategories: Attempting to delete category ${category.id} (${category.name})`);
        await this.deleteCategory(category.id);
        deletedCount++;
        console.log(`✅ deleteAllCategories: Successfully deleted category ${category.id} (${category.name})`);
      } catch (error: any) {
        const errorMsg = `Failed to delete category ${category.id} (${category.name}): ${error.message}`;
        console.error(`❌ deleteAllCategories: ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    console.log(`📊 deleteAllCategories: Deletion complete. Deleted: ${deletedCount}, Errors: ${errors.length}`);

    if (errors.length > 0 && deletedCount === 0) {
      // If no categories were deleted and there were errors, throw an error
      const errorMsg = `Failed to delete any categories. Errors: ${errors.join('; ')}`;
      console.error(`❌ deleteAllCategories: ${errorMsg}`);
      throw new Error(errorMsg);
    } else if (errors.length > 0) {
      // If some categories were deleted but there were errors, log warnings
      console.warn(`⚠️ deleteAllCategories: Some categories could not be deleted. Errors: ${errors.join('; ')}`);
    }

    console.log(`✅ deleteAllCategories: Cleanup completed. Total deleted: ${deletedCount}`);
    return deletedCount;
  }
}