// Plan pricing configuration
// TODO: Fetch pricing dynamically from API (Paddle price catalog) instead of hardcoding
export interface PlanPricing {
  readonly price: number;
  readonly popular?: boolean;
}

export const PLAN_PRICING: Readonly<Record<string, PlanPricing>> = {
  basic: { price: 0 },
  professional: { price: 9.99, popular: true },
  enterprise: { price: 29.99 },
} as const;
