import { config } from "@/config/env";
import { HttpClient } from "./httpClient";
import {
  Plan,
  PlansResponse,
  FeaturesResponse,
  PlanFeature,
  AdminSubscription,
  AdminSubscriptionsResponse,
  SubscriptionStats,
  ApiError,
} from "@/types";

export class SubscriptionService {
  private client: HttpClient;

  constructor(
    getToken: () => string | null,
    onUnauthorized?: () => void,
    onRefreshToken?: () => Promise<string | null>,
  ) {
    this.client = new HttpClient(
      config.api.subscriptionServiceUrl,
      getToken,
      onUnauthorized,
      onRefreshToken,
    );
  }

  // Admin plan endpoints
  async listPlans(): Promise<PlansResponse | ApiError> {
    return this.client.get<PlansResponse>("/v1/admin/plans");
  }

  async getPlan(planId: number): Promise<Plan | ApiError> {
    return this.client.get<Plan>(`/v1/admin/plans/${planId}`);
  }

  async updatePlanFeatures(
    planId: number,
    features: PlanFeature[],
  ): Promise<Plan | ApiError> {
    return this.client.patch<Plan>(`/v1/admin/plans/${planId}/features`, {
      features,
    });
  }

  async listFeatures(): Promise<FeaturesResponse | ApiError> {
    return this.client.get<FeaturesResponse>("/v1/admin/features");
  }

  // Admin subscription endpoints
  async listSubscriptions(params: {
    status?: string;
    planCode?: string;
    userId?: string;
    page?: number;
    pageSize?: number;
  }): Promise<AdminSubscriptionsResponse | ApiError> {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.planCode) query.set("plan_code", params.planCode);
    if (params.userId) query.set("user_id", params.userId);
    if (params.page) query.set("page", params.page.toString());
    if (params.pageSize) query.set("page_size", params.pageSize.toString());

    const queryString = query.toString();
    return this.client.get<AdminSubscriptionsResponse>(
      `/v1/admin/subscriptions${queryString ? `?${queryString}` : ""}`,
    );
  }

  async getSubscription(
    userId: string,
  ): Promise<AdminSubscription | ApiError> {
    return this.client.get<AdminSubscription>(
      `/v1/subscriptions/${userId}`,
    );
  }

  async getSubscriptionStats(): Promise<SubscriptionStats | ApiError> {
    return this.client.get<SubscriptionStats>(
      "/v1/admin/subscriptions/stats",
    );
  }

  async getHealth(): Promise<{ status: string } | ApiError> {
    return this.client.get("/health");
  }
}
