import { Category } from '@/types/category';
import { ExpenseResponse } from '@/types/expense';
import { IncomeOut } from '@/types/income';

export interface CategoryPageFilters {
  page: number;
  size: number;
  type?: 'EXPENSE' | 'INCOME' | 'all';
  search?: string;
  viewMode: 'tree' | 'table';
}

export interface CategoryUsageData {
  expenseCount: number;
  incomeCount: number;
  totalAmount: number;
  averageAmount: number;
  currency: string;
  recentExpenses: ExpenseResponse[];
  recentIncomes: IncomeOut[];
}

export const CATEGORY_TYPES = ['EXPENSE', 'INCOME'] as const;

export const CATEGORY_TYPE_I18N_MAP: Record<string, string> = {
  EXPENSE: 'category.expense',
  INCOME: 'category.income',
};

export const getTypeBadgeVariant = (type: string): string => {
  return type === 'INCOME' ? 'success' : 'destructive';
};

export const getCreatedByBadgeVariant = (createdBy?: string): string => {
  return createdBy === 'SYSTEM' ? 'secondary' : 'default';
};

export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return '\u2014';
  return new Date(dateString).toLocaleDateString('uk-UA');
};

export const getParentName = (
  parentId: number | undefined,
  categories: Category[],
): string | null => {
  if (!parentId) return null;
  const parent = categories.find((c) => c.id === parentId);
  return parent?.name || null;
};

export const buildCategoryTree = (flatCategories: Category[]): Category[] => {
  const map = new Map<number, Category>();
  const roots: Category[] = [];

  flatCategories.forEach((cat) => {
    map.set(cat.id, { ...cat, children: [] });
  });

  map.forEach((cat) => {
    if (cat.parent_id && map.has(cat.parent_id)) {
      map.get(cat.parent_id)!.children!.push(cat);
    } else {
      roots.push(cat);
    }
  });

  return roots;
};

export const flattenTree = (
  tree: Category[],
  parentName?: string,
): Array<Category & { parentName?: string }> => {
  let result: Array<Category & { parentName?: string }> = [];

  tree.forEach((cat) => {
    result.push({ ...cat, parentName });
    if (cat.children && cat.children.length > 0) {
      result = result.concat(flattenTree(cat.children, cat.name));
    }
  });

  return result;
};
