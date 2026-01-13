import { config } from '@/config/env';
import { HttpClient } from './httpClient';
import { 
  Plan, 
  PlansResponse, 
  FeaturesResponse, 
  PlanFeature,
  ApiError 
} from '@/types';

export class SubscriptionService {
  private client: HttpClient;

  constructor(getToken: () => string | null, onUnauthorized?: () => void) {
    this.client = new HttpClient(
      config.api.subscriptionServiceUrl,
      getToken,
      onUnauthorized
    );
  }

  // Admin endpoints
  async listPlans(): Promise<PlansResponse | ApiError> {
    return this.client.get<PlansResponse>('/v1/admin/plans');
  }

  async getPlan(planId: number): Promise<Plan | ApiError> {
    return this.client.get<Plan>(`/v1/admin/plans/${planId}`);
  }

  async createPlan(data: {
    code: string;
    name: string;
    period_days: number;
    is_active?: boolean;
  }): Promise<Plan | ApiError> {
    return this.client.post<Plan>('/v1/admin/plans', data);
  }

  async updatePlan(planId: number, data: {
    name?: string;
    period_days?: number;
    is_active?: boolean;
  }): Promise<Plan | ApiError> {
    return this.client.patch<Plan>(`/v1/admin/plans/${planId}`, data);
  }

  async updatePlanFeatures(planId: number, features: PlanFeature[]): Promise<Plan | ApiError> {
    return this.client.patch<Plan>(`/v1/admin/plans/${planId}/features`, { features });
  }

  async listFeatures(): Promise<FeaturesResponse | ApiError> {
    return this.client.get<FeaturesResponse>('/v1/admin/features');
  }
}
