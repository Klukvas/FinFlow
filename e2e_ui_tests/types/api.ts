// Base API types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// User types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Category types
export interface Category {
  id: number;
  name: string;
  user_id: number;
  parent_id?: number;
  type: 'EXPENSE' | 'INCOME';
  children?: Category[];
  created_at?: string;
  updated_at?: string;
}

export interface CreateCategoryRequest {
  name: string;
  parent_id?: number;
  type: 'EXPENSE' | 'INCOME';
}

export interface UpdateCategoryRequest {
  name?: string;
  parent_id?: number;
  type?: 'EXPENSE' | 'INCOME';
}

// Expense types
export interface Expense {
  id: number;
  amount: number;
  category_id?: number;
  account_id?: number;
  currency: string;
  description?: string;
  date: string;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateExpenseRequest {
  amount: number;
  category_id?: number;
  account_id?: number;
  currency?: string;
  description?: string;
  date?: string;
}

export interface UpdateExpenseRequest {
  amount?: number;
  category_id?: number;
  account_id?: number;
  currency?: string;
  description?: string;
  date?: string;
}

// Income types
export interface Income {
  id: number;
  amount: number;
  category_id?: number;
  account_id?: number;
  currency: string;
  description?: string;
  date: string;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateIncomeRequest {
  amount: number;
  category_id?: number;
  account_id?: number;
  currency?: string;
  description?: string;
  date?: string;
}

export interface UpdateIncomeRequest {
  amount?: number;
  category_id?: number;
  account_id?: number;
  currency?: string;
  description?: string;
  date?: string;
}

// Account types
export interface Account {
  id: number;
  name: string;
  balance: number;
  currency: string;
  account_type: string;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateAccountRequest {
  name: string;
  balance?: number;
  currency?: string;
  account_type: string;
}

export interface UpdateAccountRequest {
  name?: string;
  balance?: number;
  currency?: string;
  account_type?: string;
}

// Debt types
export interface Debt {
  id: number;
  amount: number;
  description?: string;
  debtor_name: string;
  due_date?: string;
  is_paid: boolean;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateDebtRequest {
  amount: number;
  description?: string;
  debtor_name: string;
  due_date?: string;
  is_paid?: boolean;
}

export interface UpdateDebtRequest {
  amount?: number;
  description?: string;
  debtor_name?: string;
  due_date?: string;
  is_paid?: boolean;
}

// Goal types
export interface Goal {
  id: number;
  title: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  target_date?: string;
  category: string;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateGoalRequest {
  title: string;
  description?: string;
  target_amount: number;
  current_amount?: number;
  target_date?: string;
  category: string;
}

export interface UpdateGoalRequest {
  title?: string;
  description?: string;
  target_amount?: number;
  current_amount?: number;
  target_date?: string;
  category?: string;
}

// Currency types
export interface Currency {
  code: string;
  name: string;
  symbol: string;
}

// Recurring types
export interface RecurringTransaction {
  id: number;
  title: string;
  description?: string;
  amount: number;
  frequency: string;
  start_date: string;
  end_date?: string;
  category_id?: number;
  account_id?: number;
  currency: string;
  transaction_type: 'INCOME' | 'EXPENSE';
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateRecurringTransactionRequest {
  title: string;
  description?: string;
  amount: number;
  frequency: string;
  start_date: string;
  end_date?: string;
  category_id?: number;
  account_id?: number;
  currency?: string;
  transaction_type: 'INCOME' | 'EXPENSE';
}

export interface UpdateRecurringTransactionRequest {
  title?: string;
  description?: string;
  amount?: number;
  frequency?: string;
  start_date?: string;
  end_date?: string;
  category_id?: number;
  account_id?: number;
  currency?: string;
  transaction_type?: 'INCOME' | 'EXPENSE';
}
