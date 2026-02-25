import { config } from "@/config/env";
import { HttpClient } from "./httpClient";
import { AdminPaymentsResponse, PaymentStats, ApiError } from "@/types";

export class PaymentService {
  private client: HttpClient;

  constructor(
    getToken: () => string | null,
    onUnauthorized?: () => void,
    onRefreshToken?: () => Promise<string | null>,
  ) {
    this.client = new HttpClient(
      config.api.paymentServiceUrl,
      getToken,
      onUnauthorized,
      onRefreshToken,
    );
  }

  async listPayments(params: {
    status?: string;
    userId?: string;
    page?: number;
    pageSize?: number;
  }): Promise<AdminPaymentsResponse | ApiError> {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.userId) query.set("user_id", params.userId);
    if (params.page) query.set("page", params.page.toString());
    if (params.pageSize) query.set("page_size", params.pageSize.toString());

    const queryString = query.toString();
    return this.client.get<AdminPaymentsResponse>(
      `/v1/admin/payments${queryString ? `?${queryString}` : ""}`,
    );
  }

  async getPaymentStats(): Promise<PaymentStats | ApiError> {
    return this.client.get<PaymentStats>("/v1/admin/payments/stats");
  }

  async getPaymentConfig(): Promise<
    { payments_enabled: boolean; service_status: string } | ApiError
  > {
    return this.client.get("/v1/config/status");
  }

  async getHealth(): Promise<{ status: string } | ApiError> {
    return this.client.get("/health/ready");
  }
}
