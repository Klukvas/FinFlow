export type CategoryType = "EXPENSE" | "INCOME";

export interface Category {
  id: number;
  name: string;
  user_id: number;
  workspace_id: string;
  parent_id?: number;
  type: CategoryType;
  monthly_budget?: number | null;
  children?: Category[];
  created_at?: string;
  updated_at?: string;
  created_by?: "USER" | "SYSTEM";
  mcc_code?: number;
  is_read_only?: boolean;
}

export interface CreateCategoryRequest {
  name: string;
  parent_id?: number;
  type: CategoryType;
  monthly_budget?: number | null;
}

export interface CreateCategoryResponse {
  id: number;
  name: string;
  user_id: number;
  parent_id?: number;
  type: CategoryType;
  children?: Category[];
  created_at?: string;
  updated_at?: string;
}

export interface CategoryListResponse {
  items: Category[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CategoryFilters {
  flat?: boolean;
  page?: number;
  size?: number;
}

export interface CategoryStatisticsResponse {
  total_categories: number;
  expense_categories: number;
  income_categories: number;
  parent_categories: number;
  child_categories: number;
}
