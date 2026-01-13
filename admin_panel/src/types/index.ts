// User types
export interface User {
  id: number;
  email: string;
  username: string;
  base_currency: string;
  role: 'user' | 'admin';
  tutorial_version: number;
}

export interface AdminUser extends User {
  status: 'active' | 'disabled';
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
