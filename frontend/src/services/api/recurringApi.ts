import { HttpClient } from './httpClient';
import { config } from '@/config/env';

const recurringApiClient = new HttpClient(config.api.recurringServiceUrl);

export interface RecurringPayment {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  amount: number;
  currency: string;
  category_id: string;
  payment_type: 'expense' | 'income';
  schedule_type: 'daily' | 'weekly' | 'monthly' | 'yearly';
  schedule_config: Record<string, any>;
  start_date: string;
  end_date?: string;
  status: 'active' | 'paused' | 'completed' | 'cancelled';
  last_executed?: string;
  next_execution: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentSchedule {
  id: string;
  recurring_payment_id: string;
  execution_date: string;
  status: 'pending' | 'executed' | 'failed';
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
  payment_type: 'EXPENSE' | 'INCOME';
  schedule_type: 'daily' | 'weekly' | 'monthly' | 'yearly';
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
  payment_type?: 'EXPENSE' | 'INCOME';
  schedule_type?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  schedule_config?: Record<string, any>;
  start_date?: string;
  end_date?: string;
  status?: 'active' | 'paused' | 'completed' | 'cancelled';
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

class RecurringApiService {
  private baseUrl = '/recurring-payments';

  // Создать повторяющийся платеж
  async createRecurringPayment(
    userId: number,
    data: CreateRecurringPaymentRequest
  ): Promise<RecurringPayment> {
    return await recurringApiClient.post(`${this.baseUrl}/?user_id=${userId}`, data);
  }

  // Получить список повторяющихся платежей
  async getRecurringPayments(
    userId: number,
    params?: {
      status?: string;
      payment_type?: string;
      page?: number;
      size?: number;
    }
  ): Promise<RecurringPaymentListResponse> {
    const queryParams = new URLSearchParams({ user_id: userId.toString() });
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.payment_type) queryParams.append('payment_type', params.payment_type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.size) queryParams.append('size', params.size.toString());

    return await recurringApiClient.get(`${this.baseUrl}/?${queryParams}`);
  }

  // Получить повторяющийся платеж по ID
  async getRecurringPayment(userId: number, paymentId: string): Promise<RecurringPayment> {
    return await recurringApiClient.get(`${this.baseUrl}/${paymentId}?user_id=${userId}`);
  }

  // Обновить повторяющийся платеж
  async updateRecurringPayment(
    userId: number,
    paymentId: string,
    data: UpdateRecurringPaymentRequest
  ): Promise<RecurringPayment> {
    return await recurringApiClient.put(`${this.baseUrl}/${paymentId}?user_id=${userId}`, data);
  }

  // Удалить повторяющийся платеж
  async deleteRecurringPayment(userId: number, paymentId: string): Promise<void> {
    await recurringApiClient.delete(`${this.baseUrl}/${paymentId}?user_id=${userId}`);
  }

  // Приостановить повторяющийся платеж
  async pauseRecurringPayment(userId: number, paymentId: string): Promise<void> {
    await recurringApiClient.post(`${this.baseUrl}/${paymentId}/pause?user_id=${userId}`);
  }

  // Возобновить повторяющийся платеж
  async resumeRecurringPayment(userId: number, paymentId: string): Promise<void> {
    await recurringApiClient.post(`${this.baseUrl}/${paymentId}/resume?user_id=${userId}`);
  }

  // Получить расписание платежа
  async getPaymentSchedules(
    userId: number,
    paymentId: string,
    params?: {
      status?: string;
      execution_date_from?: string;
      execution_date_to?: string;
      page?: number;
      size?: number;
    }
  ): Promise<PaymentScheduleListResponse> {
    const queryParams = new URLSearchParams({ user_id: userId.toString() });
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.execution_date_from) queryParams.append('execution_date_from', params.execution_date_from);
    if (params?.execution_date_to) queryParams.append('execution_date_to', params.execution_date_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.size) queryParams.append('size', params.size.toString());

    return await recurringApiClient.get(`${this.baseUrl}/${paymentId}/schedules?${queryParams}`);
  }

  // Получить статистику платежей
  async getPaymentStatistics(userId: number): Promise<PaymentStatistics> {
    return await recurringApiClient.get(`${this.baseUrl}/statistics/summary?user_id=${userId}`);
  }
}

export const recurringApiService = new RecurringApiService();
