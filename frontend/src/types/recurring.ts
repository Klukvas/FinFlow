export interface RecurringPayment {
  id: string;
  user_id: number;
  workspace_id: string;
  name: string;
  description?: string;
  amount: string;
  currency: string;
  category_id: number;
  payment_type: string;
  schedule_type: string;
  schedule_config: Record<string, any>;
  start_date: string;
  end_date?: string | null;
  status: string;
  last_executed?: string | null;
  next_execution: string;
  created_at: string;
  updated_at: string;
  is_read_only?: boolean;
}

export interface PaymentSchedule {
  id: string;
  recurring_payment_id: string;
  execution_date: string;
  status: "pending" | "executed" | "failed";
  created_expense_id: number | null;
  created_income_id: number | null;
  error_message?: string;
  executed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRecurringPaymentRequest {
  name: string;
  description?: string;
  amount: number | string;
  currency: string;
  category_id: number;
  payment_type: "EXPENSE" | "INCOME";
  schedule_type: "daily" | "weekly" | "monthly" | "yearly";
  schedule_config: Record<string, any>;
  start_date: string;
  end_date?: string | null;
}

export interface UpdateRecurringPaymentRequest {
  name?: string | null;
  description?: string | null;
  amount?: number | string | null;
  currency?: string | null;
  category_id?: number | null;
  payment_type?: string | null;
  schedule_type?: string | null;
  schedule_config?: Record<string, any> | null;
  start_date?: string | null;
  end_date?: string | null;
  status?: string | null;
}

export interface RecurringPaymentListResponse {
  items: RecurringPayment[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaymentScheduleListResponse {
  items: PaymentSchedule[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaymentStatistics {
  total_payments: number;
  active_payments: number;
  paused_payments: number;
  executed_this_month: number;
  failed_this_month: number;
}
