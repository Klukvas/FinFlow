export interface UserFeature {
  feature_code: string;
  enabled: boolean;
  limit_value: number | null;
  plan_code: string;
}

export interface UserEntitlements {
  user_id: string;
  plan_code: string;
  version: number;
  entitlements: Record<
    string,
    {
      enabled: number;
      limit_value: number | null;
    }
  >;
}

export interface PlanResponse {
  code: string;
  name: string;
  period_days: number;
  is_active: boolean;
  version: number;
}

export interface SubscriptionResponse {
  user_id: string;
  plan_code: string;
  status: "active" | "past_due" | "canceled" | "paused";
  started_at: string;
  expires_at: string | null;
  canceled_at: string | null;
  auto_renew?: boolean;
  recurring_token?: string | null;
  next_billing_date?: string | null;
  paddle_customer_id?: string | null;
  paddle_subscription_id?: string | null;
  paddle_price_id?: string | null;
}

export interface PlanFeature {
  code: string;
  name: string;
  enabled: boolean;
  limit_value: number | null;
}

export interface PlanWithFeatures {
  code: string;
  name: string;
  period_days: number;
  is_active: boolean;
  version: number;
  features: Record<string, PlanFeature>;
}
