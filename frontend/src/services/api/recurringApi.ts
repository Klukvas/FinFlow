import { AuthHttpClient, ApiError } from "./AuthHttpClient";
import { config } from "@/config/env";

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

export class RecurringApiClient {
  private httpClient: AuthHttpClient;
  private baseUrl = "/recurring-payments";

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    this.httpClient = new AuthHttpClient(
      config.api.recurringServiceUrl,
      getToken,
      refreshToken,
    );
  }

  // Создать повторяющийся платеж
  async createRecurringPayment(
    data: CreateRecurringPaymentRequest,
  ): Promise<RecurringPayment | ApiError> {
    return this.httpClient.post<RecurringPayment>(`${this.baseUrl}/`, data);
  }

  // Получить список повторяющихся платежей
  async getRecurringPayments(params?: {
    status?: string;
    payment_type?: string;
    page?: number;
    size?: number;
  }): Promise<RecurringPaymentListResponse | ApiError> {
    const queryParams = new URLSearchParams();

    if (params?.status) queryParams.append("status", params.status);
    if (params?.payment_type)
      queryParams.append("payment_type", params.payment_type);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());

    const query = queryParams.toString();
    return this.httpClient.get<RecurringPaymentListResponse>(
      `${this.baseUrl}/${query ? `?${query}` : ""}`,
    );
  }

  // Получить повторяющийся платеж по ID
  async getRecurringPayment(
    paymentId: string,
  ): Promise<RecurringPayment | ApiError> {
    return this.httpClient.get<RecurringPayment>(
      `${this.baseUrl}/${paymentId}`,
    );
  }

  // Обновить повторяющийся платеж
  async updateRecurringPayment(
    paymentId: string,
    data: UpdateRecurringPaymentRequest,
  ): Promise<RecurringPayment | ApiError> {
    return this.httpClient.put<RecurringPayment>(
      `${this.baseUrl}/${paymentId}`,
      data,
    );
  }

  // Удалить повторяющийся платеж
  async deleteRecurringPayment(paymentId: string): Promise<void | ApiError> {
    return this.httpClient.delete<void>(`${this.baseUrl}/${paymentId}`);
  }

  // Приостановить повторяющийся платеж
  async pauseRecurringPayment(paymentId: string): Promise<void | ApiError> {
    return this.httpClient.post<void>(`${this.baseUrl}/${paymentId}/pause`);
  }

  // Возобновить повторяющийся платеж
  async resumeRecurringPayment(paymentId: string): Promise<void | ApiError> {
    return this.httpClient.post<void>(`${this.baseUrl}/${paymentId}/resume`);
  }

  // Получить расписание платежа
  async getPaymentSchedules(
    paymentId: string,
    params?: {
      status?: string;
      execution_date_from?: string;
      execution_date_to?: string;
      page?: number;
      size?: number;
    },
  ): Promise<PaymentScheduleListResponse | ApiError> {
    const queryParams = new URLSearchParams();

    if (params?.status) queryParams.append("status", params.status);
    if (params?.execution_date_from)
      queryParams.append("execution_date_from", params.execution_date_from);
    if (params?.execution_date_to)
      queryParams.append("execution_date_to", params.execution_date_to);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());

    const query = queryParams.toString();
    return this.httpClient.get<PaymentScheduleListResponse>(
      `${this.baseUrl}/${paymentId}/schedules${query ? `?${query}` : ""}`,
    );
  }

  // Получить статистику платежей
  async getPaymentStatistics(): Promise<PaymentStatistics | ApiError> {
    return this.httpClient.get<PaymentStatistics>(
      `${this.baseUrl}/statistics/summary`,
    );
  }
}
