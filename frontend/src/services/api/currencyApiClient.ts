import { CurrencyHttpClient, ApiError } from "./currencyHttpClient";

export type {
  CurrencyInfo,
  ConversionRequest,
  ConversionResponse,
  CurrencyRatesResponse,
  SupportedCurrenciesResponse,
} from "@/types/currency";

import type {
  ConversionRequest,
  ConversionResponse,
  CurrencyRatesResponse,
  SupportedCurrenciesResponse,
} from "@/types/currency";

export class CurrencyApiClient {
  private httpClient: CurrencyHttpClient;

  constructor() {
    this.httpClient = new CurrencyHttpClient();
  }

  async getSupportedCurrencies(): Promise<
    SupportedCurrenciesResponse | ApiError
  > {
    return this.httpClient.get<SupportedCurrenciesResponse>(
      "/api/v1/currencies",
    );
  }

  async getCurrencyRates(
    baseCurrency: string = "USD",
  ): Promise<CurrencyRatesResponse | ApiError> {
    return this.httpClient.get<CurrencyRatesResponse>(
      `/api/v1/rates?base_currency=${baseCurrency}`,
    );
  }

  async convertCurrency(
    request: ConversionRequest,
  ): Promise<ConversionResponse | ApiError> {
    return this.httpClient.post<ConversionResponse>("/api/v1/convert", request);
  }

  async healthCheck(): Promise<
    | {
        status: string;
        timestamp: string;
        redis_connected: boolean;
        api_accessible: boolean;
      }
    | ApiError
  > {
    return this.httpClient.get("/api/v1/health");
  }
}
