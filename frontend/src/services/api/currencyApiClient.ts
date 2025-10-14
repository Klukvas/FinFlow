import { CurrencyHttpClient } from './currencyHttpClient';

export interface CurrencyInfo {
  code: string;
  name: string;
  symbol: string;
  flag: string;
  locale: string;
}

export interface ConversionRequest {
  amount: number;
  from_currency: string;
  to_currency: string;
}

export interface ConversionResponse {
  amount: number;
  converted_amount: number;
  from_currency: string;
  to_currency: string;
  rate: number;
  timestamp: string;
}

export interface CurrencyRatesResponse {
  base_currency: string;
  rates: Record<string, number>;
  timestamp: string;
}

export interface SupportedCurrenciesResponse {
  currencies: CurrencyInfo[];
  total_count: number;
}

export class CurrencyApiClient {
  private httpClient: CurrencyHttpClient;

  constructor() {
    this.httpClient = new CurrencyHttpClient();
  }

  async getSupportedCurrencies(): Promise<SupportedCurrenciesResponse> {
    return this.httpClient.get<SupportedCurrenciesResponse>('/api/v1/currencies');
  }

  async getCurrencyRates(baseCurrency: string = 'USD'): Promise<CurrencyRatesResponse> {
    return this.httpClient.get<CurrencyRatesResponse>(`/api/v1/rates?base_currency=${baseCurrency}`);
  }

  async convertCurrency(request: ConversionRequest): Promise<ConversionResponse> {
    return this.httpClient.post<ConversionResponse>('/api/v1/convert', request);
  }

  async healthCheck(): Promise<{ status: string; timestamp: string; redis_connected: boolean; api_accessible: boolean }> {
    return this.httpClient.get('/api/v1/health');
  }
}
