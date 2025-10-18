import { CategoryData } from "../types";

export async function generateCategory(type: 'EXPENSE' | 'INCOME', parentCategoryName?: string): Promise<CategoryData> {
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  const name = `Test Category ${randomSuffix}`;
  return {
    name,
    type,
    parentCategoryName
  }
}