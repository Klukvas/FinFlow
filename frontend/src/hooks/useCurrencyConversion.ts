import { useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useCurrency } from "@/contexts/CurrencyContext";
import { logger } from "@/utils/logger";

interface UseCurrencyConversionReturn {
  userCurrency: string;
  exchangeRates: Record<string, number>;
  isLoadingRates: boolean;
  convertToUserCurrency: (
    amount: number,
    fromCurrency: string,
  ) => number | null;
  formatCurrency: (amount: number, currency?: string) => string;
}

export const useCurrencyConversion = (): UseCurrencyConversionReturn => {
  const { user } = useAuth();
  const { currencies, exchangeRates, isLoadingRates } = useCurrency();

  const userCurrency = user?.base_currency || "USD";

  const convertToUserCurrency = useCallback(
    (amount: number, fromCurrency: string): number | null => {
      if (fromCurrency === userCurrency) {
        return amount;
      }

      const rate = exchangeRates[fromCurrency];
      if (!rate) {
        logger.warn(
          `Exchange rate not available for ${fromCurrency} -> ${userCurrency}`,
        );
        return null;
      }

      return amount / rate;
    },
    [userCurrency, exchangeRates],
  );

  const formatCurrency = useCallback(
    (amount: number, currency: string = userCurrency): string => {
      const currencyInfo = currencies.find((c) => c.code === currency);
      const locale = currencyInfo?.locale || "en-US";
      return new Intl.NumberFormat(locale, {
        style: "currency",
        currency: currency,
      }).format(amount);
    },
    [userCurrency, currencies],
  );

  return {
    userCurrency,
    exchangeRates,
    isLoadingRates,
    convertToUserCurrency,
    formatCurrency,
  };
};
