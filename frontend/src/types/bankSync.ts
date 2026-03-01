export interface LinkedAccount {
  id: number;
  external_account_id: string;
  account_name: string | null;
  currency: string | null;
  currency_code: number | null;
  masked_pan: string | null;
  iban: string | null;
  finflow_account_id: number | null;
  is_synced: boolean;
}

export interface BankConnection {
  id: number;
  bank_type: string;
  client_name: string | null;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string | null;
  accounts: LinkedAccount[];
}

export interface SyncStatus {
  id: number;
  status: string;
  transactions_found: number;
  transactions_imported: number;
  transactions_skipped: number;
  error_message: string | null;
  sync_from: string | null;
  sync_to: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface SyncRequest {
  account_ids?: number[];
  days_back?: number;
}

export interface LinkAccountRequest {
  finflow_account_id: number;
}

export interface ConnectionCreate {
  token: string;
}

export interface SyncPreviewTransaction {
  external_id: string;
  type: "expense" | "income";
  amount: number;
  currency: string;
  date: string;
  description: string;
  mcc: number | null;
  category_id: number | null;
  category_name: string | null;
  account_id: number;
}

export interface SyncPreviewResponse {
  transactions: SyncPreviewTransaction[];
  total_found: number;
  total_new: number;
  total_skipped: number;
}

export interface SyncConfirmTransaction {
  external_id: string;
  type: "expense" | "income";
  amount: number;
  currency: string;
  date: string;
  description: string;
  category_id: number | null;
  account_id: number;
}
