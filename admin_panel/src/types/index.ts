// User types
export interface User {
  id: number;
  email: string;
  username: string;
  base_currency: string;
  role: "user" | "admin";
  tutorial_version: number;
}

export interface AdminUser extends User {
  status: "active" | "disabled";
  created_at: string | null;
}

export interface AdminUsersResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Subscription types
export interface PlanFeature {
  feature_code: string;
  enabled: boolean;
  limit_value: number | null;
}

export interface Plan {
  id: number;
  code: string;
  name: string;
  period_days: number;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
  features: PlanFeature[];
}

export interface PlansResponse {
  items: Plan[];
}

export interface Feature {
  code: string;
  name: string;
  description: string | null;
}

export interface FeaturesResponse {
  items: Feature[];
}

// API types
export interface ApiError {
  error: string;
  status?: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Admin Subscription types
export interface AdminSubscription {
  id: number;
  user_id: string;
  plan_code: string;
  status: string;
  started_at: string;
  expires_at: string | null;
  canceled_at: string | null;
  auto_renew: boolean;
  payment_provider: string | null;
  last_payment_id: string | null;
  next_billing_date: string | null;
  paddle_customer_id: string | null;
  paddle_subscription_id: string | null;
  paddle_price_id: string | null;
  cancellation_reason: string | null;
  cancellation_comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminSubscriptionsResponse {
  items: AdminSubscription[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SubscriptionStats {
  total: number;
  active: number;
  past_due: number;
  canceled: number;
  paused: number;
}

// Admin Payment types
export interface PaymentEvent {
  id: string;
  payment_id: string;
  event_type: string;
  provider_event_id: string | null;
  signature_valid: boolean | null;
  status_before: string | null;
  status_after: string | null;
  created_at: string;
}

export interface AdminPayment {
  id: string;
  provider: string;
  order_reference: string;
  user_id: string;
  workspace_id: string | null;
  purpose: string;
  plan_code: string | null;
  amount: string;
  currency: string;
  status: string;
  provider_payment_url: string | null;
  paid_at: string | null;
  failed_at: string | null;
  refunded_at: string | null;
  failure_reason: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  events: PaymentEvent[];
}

export interface AdminPaymentsResponse {
  items: AdminPayment[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaymentStats {
  total: number;
  by_status: Record<string, number>;
  total_revenue: string;
}

// Service Health types
export interface ServiceHealth {
  name: string;
  url: string;
  status: "up" | "down" | "loading";
  detail?: string;
}
