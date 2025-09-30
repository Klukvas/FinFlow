import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export interface ParsedTransaction {
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: 'income' | 'expense';
  bank_type: string;
  raw_text?: string;
  confidence_score: number;
}

export interface PDFParseResponse {
  transactions: ParsedTransaction[];
  bank_detected: string;
  total_transactions: number;
  successful_parses: number;
  failed_parses: number;
  parsing_metadata: {
    file_size: number;
    parsing_method: string;
    confidence_threshold: number;
  };
}

export interface TransactionValidation {
  transaction_id: string;
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: 'income' | 'expense';
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
  banks: Record<string, {
    available_languages: LanguageInfo[];
    total_languages: number;
  }>;
  total_banks: number;
}

export type ApiResponse<T> = T | ApiError;

export class PDFParserApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.pdfParserServiceUrl}/pdf`,
      getToken,
      refreshToken
    );
  }

  async parsePDF(
    file: File,
    bankType?: string
  ): Promise<ApiResponse<PDFParseResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    if (bankType) {
      formData.append('bank_type', bankType);
    }

    console.log('API Client - Sending FormData:', {
      hasFile: formData.has('file'),
      fileSize: file.size,
      bankType: bankType || 'none',
      formDataEntries: Array.from(formData.entries())
    });

    return this.httpClient.post<PDFParseResponse>('/parse', formData);
  }

  async getSupportedBanks(): Promise<ApiResponse<{ supported_banks: string[]; total_count: number }>> {
    return this.httpClient.get<{ supported_banks: string[]; total_count: number }>('/supported-banks');
  }

  async getBankLanguages(bankName: string): Promise<ApiResponse<BankLanguagesResponse>> {
    return this.httpClient.get<BankLanguagesResponse>(`/languages/${bankName}`);
  }

  async getAllLanguages(): Promise<ApiResponse<AllLanguagesResponse>> {
    return this.httpClient.get<AllLanguagesResponse>('/languages');
  }

  async healthCheck(): Promise<ApiResponse<{ status: string; service: string; supported_banks: number }>> {
    return this.httpClient.get<{ status: string; service: string; supported_banks: number }>('/health');
  }

  // Utility methods
  async getBankInfo(bankName: string): Promise<ApiResponse<BankLanguagesResponse & { supported_banks: string[] }>> {
    const [languagesResponse, banksResponse] = await Promise.all([
      this.getBankLanguages(bankName),
      this.getSupportedBanks()
    ]);

    if ('error' in languagesResponse) {
      return languagesResponse;
    }

    if ('error' in banksResponse) {
      return banksResponse;
    }

    return {
      ...languagesResponse,
      supported_banks: banksResponse.supported_banks
    };
  }

  // Helper method to check if a bank is supported
  async isBankSupported(bankName: string): Promise<boolean> {
    try {
      const response = await this.getSupportedBanks();
      if ('error' in response) {
        return false;
      }
      return response.supported_banks
        .map(bank => bank.toLowerCase())
        .includes(bankName.toLowerCase());
    } catch {
      return false;
    }
  }
}
