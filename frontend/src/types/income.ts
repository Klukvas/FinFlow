export interface IncomeCreate {
  amount: number;
  category_id?: number | null;
  account_id?: number | null;
  currency?: string;
  description?: string | null;
  date?: string | null;
}

export interface IncomeOut {
  id: number;
  user_id: number;
  amount: number;
  category_id?: number | null;
  account_id?: number | null;
  currency: string;
  description?: string | null;
  date: string;
  created_at: string;
  updated_at: string;
}

export interface IncomeUpdate {
  amount?: number | null;
  category_id?: number | null;
  account_id?: number | null;
  currency?: string | null;
  description?: string | null;
  date?: string | null;
}

export interface IncomeSummary {
  total_income: number;
  count: number;
  average_income: number;
  period_start: string;
  period_end: string;
}

export interface IncomeStats {
  total_income: number;
  monthly_income: number;
  yearly_income: number;
  income_count: number;
  average_income: number;
}

export interface CreateIncomeRequest {
  amount: number;
  category_id?: number;
  account_id?: number;
  description: string;
  date: string;
}
