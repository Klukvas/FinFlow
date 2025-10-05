/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_CATEGORY_SERVICE_URL: string
  readonly VITE_EXPENSE_SERVICE_URL: string
  readonly VITE_INCOME_SERVICE_URL: string
  readonly VITE_RECURRING_SERVICE_URL: string
  readonly VITE_GOALS_SERVICE_URL: string
  readonly VITE_PDF_PARSER_SERVICE_URL: string
  readonly VITE_DEBT_SERVICE_URL: string
  readonly VITE_ACCOUNT_SERVICE_URL: string
  readonly VITE_CURRENCY_SERVICE_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_DEBUG: string
  readonly DEV: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
