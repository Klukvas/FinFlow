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
