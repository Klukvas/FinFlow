// Import contact types
import { ContactResponse } from "./contact";

export type DebtType =
  | "CREDIT_CARD"
  | "LOAN"
  | "MORTGAGE"
  | "PERSONAL_LOAN"
  | "AUTO_LOAN"
  | "STUDENT_LOAN"
  | "OTHER";

export type PaymentMethod =
  | "CASH"
  | "CARD"
  | "TRANSFER"
  | "CHECK"
  | "AUTOMATIC"
  | "OTHER";

// Debt Interfaces
export interface DebtCreate {
  name: string;
  description?: string | null;
  debt_type: DebtType;
  contact_id?: number | null;
  category_id?: number | null;
  currency: string;
  initial_amount: number;
  interest_rate?: number | null;
  minimum_payment?: number | null;
  start_date: string;
  due_date?: string | null;
}

export interface DebtUpdate {
  name?: string | null;
  description?: string | null;
  debt_type?: DebtType | null;
  contact_id?: number | null;
  category_id?: number | null;
  currency?: string | null;
  interest_rate?: number | null;
  minimum_payment?: number | null;
  due_date?: string | null;
  is_active?: boolean | null;
  is_paid_off?: boolean | null;
}

export interface DebtResponse {
  id: number;
  user_id: number;
  workspace_id: string;
  name: string;
  description?: string | null;
  debt_type: DebtType;
  contact_id?: number | null;
  category_id?: number | null;
  currency: string;
  initial_amount: number;
  current_balance: number;
  interest_rate?: number | null;
  minimum_payment?: number | null;
  start_date: string;
  due_date?: string | null;
  last_payment_date?: string | null;
  is_active: boolean;
  is_paid_off: boolean;
  created_at: string;
  updated_at: string;
  contact?: ContactResponse | null;
  payment_count?: number; // Number of payments for this debt
  is_read_only?: boolean;
}

// Debt Payment Interfaces
export interface DebtPaymentCreate {
  amount: number;
  principal_amount?: number | null;
  interest_amount?: number | null;
  payment_date: string;
  description?: string | null;
  payment_method?: PaymentMethod | null;
}

export interface DebtPaymentResponse {
  id: number;
  debt_id: number;
  user_id: number;
  amount: number;
  principal_amount?: number | null;
  interest_amount?: number | null;
  payment_date: string;
  description?: string | null;
  payment_method?: PaymentMethod | null;
  created_at: string;
  updated_at: string;
}

// Summary Interfaces
export interface DebtSummary {
  total_debt: number;
  total_payments: number;
  active_debts: number;
  paid_off_debts: number;
  currency: string;
  average_interest_rate?: number | null;
}
