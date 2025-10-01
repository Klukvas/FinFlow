export interface ExpenseCreate {
    amount: number;
    category_id: number;
    account_id?: number | null;
    currency?: string;
    description?: string | null;
    date?: string | null;
  }
  
  export interface ExpenseResponse {
    id: number;
    amount: number;
    category_id: number;
    account_id?: number | null;
    currency: string;
    description: string;
    date: string;
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
  
  export interface ErrorResponse {
    error: string;
  }
  
  export interface CreateExpenseRequest {
    amount: number;
    category_id: number;
    account_id?: number;
    currency?: string;
    description: string;
    date: string;
  }