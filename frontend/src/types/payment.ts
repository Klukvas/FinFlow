// Payment types matching backend payment_service

export enum PaymentStatus {
  CREATED = 'CREATED',
  PENDING = 'PENDING',
  PAID = 'PAID',
  FAILED = 'FAILED',
  EXPIRED = 'EXPIRED',
  REFUNDED = 'REFUNDED',
  PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED',
  CANCELED = 'CANCELED',
}

export enum PaymentProvider {
  WAYFORPAY = 'WAYFORPAY',
}

export enum PaymentPurpose {
  SUBSCRIPTION = 'SUBSCRIPTION',
  ONE_TIME = 'ONE_TIME',
}

export interface CreatePaymentRequest {
  user_id: string;
  workspace_id?: string;
  purpose: PaymentPurpose;
  plan_code?: string;
  amount: number;
  currency: string;
  return_url?: string;
  metadata?: Record<string, any>;
}

export interface CreatePaymentResponse {
  payment_id: string;
  order_reference: string;
  provider: PaymentProvider;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_url: string;
  provider_form_fields?: Record<string, any>;
  created_at: string;
}

export interface PaymentEvent {
  id: string;
  payment_id: string;
  event_type: string;
  provider_event_id?: string;
  signature_valid?: boolean;
  status_before?: string;
  status_after?: string;
  created_at: string;
}

export interface Payment {
  id: string;
  provider: PaymentProvider;
  order_reference: string;
  user_id: string;
  workspace_id?: string;
  purpose: PaymentPurpose;
  plan_code?: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  provider_payment_url?: string;
  paid_at?: string;
  failed_at?: string;
  refunded_at?: string;
  failure_reason?: string;
  extra_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
  events?: PaymentEvent[];
}

export interface PaymentHistoryFilters {
  status?: PaymentStatus;
  purpose?: PaymentPurpose;
  limit?: number;
  offset?: number;
}

// UI-specific types
export interface PaymentUIState {
  isProcessing: boolean;
  currentPayment?: Payment;
  error?: string;
}
