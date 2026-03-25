import { AuthHttpClient, ApiError } from "./AuthHttpClient";
import { config } from "@/config/env";

export type {
  RecurringPayment,
  PaymentSchedule,
  CreateRecurringPaymentRequest,
  UpdateRecurringPaymentRequest,
  RecurringPaymentListResponse,
  PaymentScheduleListResponse,
  PaymentStatistics,
} from "@/types/recurring";

import type {
  RecurringPayment,
  CreateRecurringPaymentRequest,
  UpdateRecurringPaymentRequest,
  RecurringPaymentListResponse,
  PaymentScheduleListResponse,
  PaymentStatistics,
} from "@/types/recurring";

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
