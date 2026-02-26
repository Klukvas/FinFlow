export interface AccountCreate {
  name: string;
  type: string;
  currency: string;
  balance: number;
}

export interface AccountUpdate {
  name?: string;
  type?: string;
  currency?: string;
  balance?: number;
}

export interface AccountResponse {
  id: number;
  name: string;
  type: string;
  currency: string;
  balance: number;
  user_id: number;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  is_read_only?: boolean;
}

export interface AccountSummary {
  id: number;
  name: string;
  type: string;
  currency: string;
  balance: number;
  transaction_count: number;
  last_transaction_date?: string;
}

export interface AccountTransactionSummary {
  account: AccountResponse;
  total_income: number;
  total_expenses: number;
  net_balance: number;
  transaction_count: number;
  recent_transactions: Array<{
    id: number;
    type: "income" | "expense";
    amount: number;
    description: string;
    date: string;
  }>;
}

export interface CreateAccountRequest {
  name: string;
  type: string;
  currency: string;
  balance: number;
}

export interface AccountStatisticsResponse {
  total_accounts: number;
  active_accounts: number;
  total_balance: number;
  currency: string;
  unconvertible_accounts_count: number;
}
