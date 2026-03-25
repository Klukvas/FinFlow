export interface ParsedTransaction {
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: "income" | "expense";
  bank_type: string;
  raw_text?: string;
  confidence_score: number;
  mcc_code?: number;
  mcc_category_name?: string;
  mcc_category_translation?: string;
  category_exists: boolean | null;
  category_id?: number;
}

export interface PDFLimitInfo {
  uploads_per_month: number | null; // null = unlimited
  records_per_upload: number | null; // null = unlimited
  uploads_used_this_month: number;
  uploads_remaining: number | null; // null = unlimited
  plan_code: string;
}

export interface PDFParseResponse {
  transactions: ParsedTransaction[];
  bank_detected: string;
  total_transactions: number;
  successful_parses: number;
  failed_parses: number;
  parsing_metadata: Record<string, unknown> | null;
  limit_info?: PDFLimitInfo;
}

export interface TransactionValidation {
  transaction_id: string;
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: "income" | "expense";
  category_id?: number;
  is_valid: boolean;
}

export interface BatchCreateRequest {
  transactions: TransactionValidation[];
  user_id: number;
}

export interface BatchCreateResponse {
  created_income_count: number;
  created_expense_count: number;
  failed_transactions: any[];
  success: boolean;
}

export interface LanguageInfo {
  code: string;
  name: string;
  headers_count: number;
}

export interface BankLanguagesResponse {
  bank: string;
  available_languages: LanguageInfo[];
  total_languages: number;
}

export interface AllLanguagesResponse {
  banks: Record<
    string,
    {
      available_languages: LanguageInfo[];
      total_languages: number;
    }
  >;
  total_banks: number;
}
