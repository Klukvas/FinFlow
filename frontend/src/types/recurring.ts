export interface RecurringPayment {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  amount: number;
  currency: string;
  category_id: string;
  payment_type: "expense" | "income";
  schedule_type: "daily" | "weekly" | "monthly" | "yearly";
  schedule_config: Record<string, any>;
  start_date: string;
  end_date?: string;
  status: "active" | "paused" | "completed" | "cancelled";
  last_executed?: string;
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
  created_expense_id?: string;
  created_income_id?: string;
  error_message?: string;
  executed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRecurringPaymentRequest {
  name: string;
  description?: string;
  amount: number;
  currency: string;
  category_id: number;
  payment_type: "EXPENSE" | "INCOME";
  schedule_type: "daily" | "weekly" | "monthly" | "yearly";
  schedule_config: Record<string, any>;
  start_date: string;
  end_date?: string;
}

export interface UpdateRecurringPaymentRequest {
  name?: string;
  description?: string;
  amount?: number;
  currency?: string;
  category_id?: number;
  payment_type?: "EXPENSE" | "INCOME";
  schedule_type?: "daily" | "weekly" | "monthly" | "yearly";
  schedule_config?: Record<string, any>;
  start_date?: string;
  end_date?: string;
  status?: "active" | "paused" | "completed" | "cancelled";
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
