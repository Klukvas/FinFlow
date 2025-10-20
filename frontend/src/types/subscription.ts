export interface UserFeature {
  feature_code: string;
  enabled: boolean;
  limit_value: number | null;
}

export interface UserEntitlements {
  user_id: string;
  plan_code: string;
  version: number;
  entitlements: Record<string, {
    enabled: number;
    limit_value: number;
  }>;
}

export interface PlanResponse {
  id: number;
  code: string;
  name: string;
  period_days: number;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionResponse {
  user_id: number;
  plan_code: string;
  status: 'active' | 'past_due' | 'canceled' | 'paused';
  started_at: string;
  expires_at: string | null;
  canceled_at: string | null;
}
