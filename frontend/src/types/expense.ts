export interface ExpenseCreate {
  amount: number;
  category_id?: number | null;
  account_id?: number | null;
  currency?: string | null;
  description?: string | null;
  date?: string | null;
}

export interface ExpenseResponse {
  id: number;
  amount: number;
  category_id?: number | null;
  account_id?: number | null;
  currency?: string | null;
  description?: string | null;
  date?: string | null;
  user_id: number;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export interface ExpenseUpdate {
  amount?: number | null;
  category_id?: number | null;
  account_id?: number | null;
  currency?: string | null;
  description?: string | null;
  date?: string | null;
}

export interface CreateExpenseRequest {
  amount: number;
  category_id?: number | undefined;
  account_id?: number | undefined;
  currency?: string;
  description: string;
  date: string;
}

export interface ExpenseListResponse {
  items: ExpenseResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ExpenseFilters {
  page?: number;
  size?: number;
  category_ids?: number[];
  account_id?: number;
  currency?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: "date" | "amount" | "category";
  sort_order?: "asc" | "desc";
}

export interface CategoryExpenseStatistics {
  total_amount: number;
  count: number;
  average_amount: number;
  currency: string;
}

export interface ExpensesByCategoryResponse {
  expenses: ExpenseResponse[];
  statistics: CategoryExpenseStatistics;
}
