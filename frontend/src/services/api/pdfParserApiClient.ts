import { AuthHttpClient, ApiError } from "./AuthHttpClient";
import { config } from "@/config/env";

export type {
  ParsedTransaction,
  PDFLimitInfo,
  PDFParseResponse,
  TransactionValidation,
  BatchCreateRequest,
  BatchCreateResponse,
  LanguageInfo,
  BankLanguagesResponse,
  AllLanguagesResponse,
} from "@/types/pdfParser";

import type {
  PDFParseResponse,
  BankLanguagesResponse,
  AllLanguagesResponse,
} from "@/types/pdfParser";

export type ApiResponse<T> = T | ApiError;

export class PDFParserApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.pdfParserServiceUrl}/pdf`,
      getToken,
      refreshToken,
    );
  }

  async parsePDF(
    file: File,
    bankType?: string,
    language?: string,
  ): Promise<ApiResponse<PDFParseResponse>> {
    const formData = new FormData();
    formData.append("file", file);
    if (bankType) {
      formData.append("bank_type", bankType);
    }
    if (language) {
      formData.append("language", language);
    }

    return this.httpClient.post<PDFParseResponse>("/parse", formData);
  }

  async getSupportedBanks(): Promise<
    ApiResponse<{ supported_banks: string[]; total_count: number }>
  > {
    return this.httpClient.get<{
      supported_banks: string[];
      total_count: number;
    }>("/supported-banks");
  }

  async getBankLanguages(
    bankName: string,
  ): Promise<ApiResponse<BankLanguagesResponse>> {
    return this.httpClient.get<BankLanguagesResponse>(`/languages/${bankName}`);
  }

  async getAllLanguages(): Promise<ApiResponse<AllLanguagesResponse>> {
    return this.httpClient.get<AllLanguagesResponse>("/languages");
  }

  async healthCheck(): Promise<
    ApiResponse<{ status: string; service: string; supported_banks: number }>
  > {
    return this.httpClient.get<{
      status: string;
      service: string;
      supported_banks: number;
    }>("/health");
  }

  // Utility methods
  async getBankInfo(
    bankName: string,
  ): Promise<
    ApiResponse<BankLanguagesResponse & { supported_banks: string[] }>
  > {
    const [languagesResponse, banksResponse] = await Promise.all([
      this.getBankLanguages(bankName),
      this.getSupportedBanks(),
    ]);

    if ("error" in languagesResponse) {
      return languagesResponse;
    }

    if ("error" in banksResponse) {
      return banksResponse;
    }

    return {
      ...languagesResponse,
      supported_banks: banksResponse.supported_banks,
    };
  }

  // Helper method to check if a bank is supported
  async isBankSupported(bankName: string): Promise<boolean> {
    try {
      const response = await this.getSupportedBanks();
      if ("error" in response) {
        return false;
      }
      return response.supported_banks
        .map((bank) => bank.toLowerCase())
        .includes(bankName.toLowerCase());
    } catch {
      return false;
    }
  }
}
