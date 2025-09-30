// Environment configuration
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
    categoryServiceUrl: import.meta.env.VITE_CATEGORY_SERVICE_URL || 'http://localhost:8002',
    expenseServiceUrl: import.meta.env.VITE_EXPENSE_SERVICE_URL || 'http://localhost:8003',
    incomeServiceUrl: import.meta.env.VITE_INCOME_SERVICE_URL || 'http://localhost:8004',
    recurringServiceUrl: import.meta.env.VITE_RECURRING_SERVICE_URL || 'http://localhost:8005',
    goalsServiceUrl: import.meta.env.VITE_GOALS_SERVICE_URL || 'http://localhost:8006',
    pdfParserServiceUrl: import.meta.env.VITE_PDF_PARSER_SERVICE_URL || 'http://localhost:8007',
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'Financial Accounting',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  },
  debug: import.meta.env.VITE_DEBUG === 'true' || import.meta.env.DEV,
} as const;

export type Config = typeof config;
