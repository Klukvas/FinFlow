export interface ExpenseCreate {
    amount: number;
    category_id: number;
    description?: string | null;
    date?: string | null;
  }
  
  export interface ExpenseResponse {
    id: number;
    amount: number;
    category_id: number;
    description: string;
    date: string;
    created_at: string;
    updated_at: string;
  }
  
  export interface ExpenseUpdate {
    amount?: number | null;
    category_id?: number | null;
    description?: string | null;
    date?: string | null;
  }
  
  export interface ErrorResponse {
    error: string;
  }
  
  export interface CreateExpenseRequest {
    amount: number;
    category_id: number;
    description: string;
    date: string;
  }