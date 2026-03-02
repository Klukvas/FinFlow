export interface AccountCreate {
  name: string;
  type: string;
  currency: string;
  balance: number;
  description?: string | null;
}

export interface AccountUpdate {
  name?: string;
  type?: string;
  currency?: string;
  balance?: number;
  description?: string | null;
  is_active?: boolean | null;
}

export interface AccountResponse {
  id: number;
  name: string;
  type: string;
  currency: string;
  balance: number;
  description?: string | null;
  owner_id: number;
  user_id: number;
  workspace_id: string;
  is_active: boolean;
  is_archived: boolean;
  is_read_only?: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountSummary {
  id: number;
  name: string;
  type: string;
  currency: string;
  balance: number;
  is_active: boolean;
  transaction_count: number;
  last_transaction_date?: string;
}

export interface AccountTransaction {
  id: number;
  amount: number;
  description?: string | null;
  date: string;
  type: string;
  category_id?: number | null;
  category_name?: string | null;
}

export interface AccountTransactionSummary {
  account: AccountSummary;
  transactions: AccountTransaction[];
  total_income: number;
  total_expenses: number;
  net_change: number;
}

export interface CreateAccountRequest {
  name: string;
  type: string;
  currency: string;
  balance: number;
  description?: string | null;
}

export interface AccountStatisticsResponse {
  total_accounts: number;
  active_accounts: number;
  total_balance: number;
  currency: string;
  unconvertible_accounts_count: number;
}
