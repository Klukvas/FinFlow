// Environment configuration
export const config = {
  api: {
    // In production, Caddy routes /api/* to the correct service
    // In development, use localhost ports
    baseUrl:
      import.meta.env.VITE_API_BASE_URL ||
      (import.meta.env.PROD ? "/api/users" : "http://localhost:8001"),
    categoryServiceUrl:
      import.meta.env.VITE_CATEGORY_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/categories" : "http://localhost:8002"),
    expenseServiceUrl:
      import.meta.env.VITE_EXPENSE_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/expenses" : "http://localhost:8003"),
    incomeServiceUrl:
      import.meta.env.VITE_INCOME_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/income" : "http://localhost:8004"),
    recurringServiceUrl:
      import.meta.env.VITE_RECURRING_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/recurring" : "http://localhost:8005"),
    goalsServiceUrl:
      import.meta.env.VITE_GOALS_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/goals" : "http://localhost:8006"),
    pdfParserServiceUrl:
      import.meta.env.VITE_PDF_PARSER_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/pdf" : "http://localhost:8007"),
    debtServiceUrl:
      import.meta.env.VITE_DEBT_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/debts" : "http://localhost:8008"),
    accountServiceUrl:
      import.meta.env.VITE_ACCOUNT_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/accounts" : "http://localhost:8009"),
    currencyServiceUrl:
      import.meta.env.VITE_CURRENCY_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/currencies" : "http://localhost:8010"),
    subscriptionServiceUrl:
      import.meta.env.VITE_SUBSCRIPTION_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/subscriptions" : "http://localhost:8011"),
    workspaceServiceUrl:
      import.meta.env.VITE_WORKSPACE_SERVICE_URL ||
      (import.meta.env.PROD
        ? "/api/workspaces"
        : "http://localhost:8012/workspaces"),
    paymentServiceUrl:
      import.meta.env.VITE_PAYMENT_SERVICE_URL ||
      (import.meta.env.PROD ? "/api/payments" : "http://localhost:8013"),
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || "FinFlow",
    version: import.meta.env.VITE_APP_VERSION || "1.0.0",
  },
  paddle: {
    clientToken: import.meta.env.VITE_PADDLE_CLIENT_TOKEN || "",
    environment: (import.meta.env.VITE_PADDLE_ENVIRONMENT || "sandbox") as
      | "sandbox"
      | "production",
  },
  features: {
    // Payments are disabled by default until Paddle integration is configured
    paymentsEnabled: import.meta.env.VITE_PAYMENTS_ENABLED === "true",
  },
  debug: import.meta.env.VITE_DEBUG === "true" || import.meta.env.DEV,
} as const;

export type Config = typeof config;
