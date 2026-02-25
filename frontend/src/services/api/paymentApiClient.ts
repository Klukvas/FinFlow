import {
  CreatePaymentRequest,
  CreatePaymentResponse,
  ChangePlanRequest,
  ChangePlanResponse,
  Payment,
  PaymentHistoryFilters,
} from "@/types/payment";
import { AuthHttpClient } from "./AuthHttpClient";
import { config } from "@/config/env";

export interface PaymentErrorResponse {
  error: string;
}

export class PaymentApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    const baseUrl = config.api.paymentServiceUrl || "http://localhost:8013";
    this.httpClient = new AuthHttpClient(
      `${baseUrl}/v1`,
      getToken,
      refreshToken,
      true, // skip workspace header for payment service
    );
  }

  /**
   * Create a new payment
   */
  async createPayment(
    request: CreatePaymentRequest,
    idempotencyKey?: string,
  ): Promise<CreatePaymentResponse | PaymentErrorResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }

    return this.httpClient.post<CreatePaymentResponse>(
      "/payments",
      request,
      headers,
    );
  }

  /**
   * Get payment by ID
   */
  async getPayment(paymentId: string): Promise<Payment | PaymentErrorResponse> {
    return this.httpClient.get<Payment>(`/payments/${paymentId}`);
  }

  /**
   * Get payment by order reference
   */
  async getPaymentByOrderRef(
    orderReference: string,
  ): Promise<Payment | PaymentErrorResponse> {
    return this.httpClient.get<Payment>(`/payments/by-order/${orderReference}`);
  }

  /**
   * List user's payments
   */
  async listPayments(
    filters: PaymentHistoryFilters = {},
  ): Promise<Payment[] | PaymentErrorResponse> {
    const params = new URLSearchParams();
    if (filters.limit) params.append("limit", filters.limit.toString());
    if (filters.offset) params.append("offset", filters.offset.toString());

    const queryString = params.toString();
    const endpoint = `/payments${queryString ? `?${queryString}` : ""}`;

    return this.httpClient.get<Payment[]>(endpoint);
  }

  /**
   * Change subscription plan (upgrade/downgrade) via Paddle API
   */
  async changePlan(
    request: ChangePlanRequest,
  ): Promise<ChangePlanResponse | PaymentErrorResponse> {
    return this.httpClient.post<ChangePlanResponse>(
      "/payments/change-plan",
      request,
    );
  }

  /**
   * Poll payment status (for checking after redirect)
   */
  async pollPaymentStatus(
    paymentId: string,
    maxAttempts: number = 30,
    intervalMs: number = 5000,
  ): Promise<Payment | PaymentErrorResponse> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const result = await this.getPayment(paymentId);

      if ("error" in result) {
        return result;
      }

      // If payment is in terminal state, return it
      if (["PAID", "FAILED", "EXPIRED", "CANCELED"].includes(result.status)) {
        return result;
      }

      // Wait before next attempt
      if (attempt < maxAttempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    }

    return {
      error: "Payment status polling timeout",
    };
  }
}
