import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import {
  CurrencyApiClient,
  CurrencyInfo,
} from "@/services/api/currencyApiClient";
import { useAuth } from "./AuthContext";
import { logger } from "@/utils/logger";

interface CurrencyContextType {
  currencies: CurrencyInfo[];
  exchangeRates: Record<string, number>;
  isLoading: boolean;
  isLoadingRates: boolean;
  error: string | null;
  refreshCurrencies: () => Promise<void>;
  refreshRates: () => Promise<void>;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(
  undefined,
);

interface CurrencyProviderProps {
  children: ReactNode;
}

export const CurrencyProvider: React.FC<CurrencyProviderProps> = ({
  children,
}) => {
  const { user } = useAuth();
  const [currencies, setCurrencies] = useState<CurrencyInfo[]>([]);
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>(
    {},
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRates, setIsLoadingRates] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrencies = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const currencyClient = new CurrencyApiClient();
      const response = await currencyClient.getSupportedCurrencies();
      setCurrencies(response.currencies);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch currencies";
      setError(errorMessage);
      logger.error("Failed to fetch currencies:", err);

      // Fallback to basic currencies if API fails
      setCurrencies([
        {
          code: "USD",
          name: "US Dollar",
          symbol: "$",
          flag: "🇺🇸",
          locale: "en-US",
        },
        { code: "EUR", name: "Euro", symbol: "€", flag: "🇪🇺", locale: "de-DE" },
        {
          code: "GBP",
          name: "British Pound",
          symbol: "£",
          flag: "🇬🇧",
          locale: "en-GB",
        },
        {
          code: "JPY",
          name: "Japanese Yen",
          symbol: "¥",
          flag: "🇯🇵",
          locale: "ja-JP",
        },
        {
          code: "CHF",
          name: "Swiss Franc",
          symbol: "CHF",
          flag: "🇨🇭",
          locale: "de-CH",
        },
        {
          code: "CAD",
          name: "Canadian Dollar",
          symbol: "C$",
          flag: "🇨🇦",
          locale: "en-CA",
        },
        {
          code: "AUD",
          name: "Australian Dollar",
          symbol: "A$",
          flag: "🇦🇺",
          locale: "en-AU",
        },
        {
          code: "CNY",
          name: "Chinese Yuan",
          symbol: "¥",
          flag: "🇨🇳",
          locale: "zh-CN",
        },
        {
          code: "UAH",
          name: "Ukrainian Hryvnia",
          symbol: "₴",
          flag: "🇺🇦",
          locale: "uk-UA",
        },
        {
          code: "RUB",
          name: "Russian Ruble",
          symbol: "₽",
          flag: "🇷🇺",
          locale: "ru-RU",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCurrencies = async () => {
    await fetchCurrencies();
  };

  const fetchExchangeRates = async () => {
    if (!user?.base_currency) return;

    setIsLoadingRates(true);
    try {
      const currencyClient = new CurrencyApiClient();
      const response = await currencyClient.getCurrencyRates(
        user.base_currency,
      );
      setExchangeRates(response.rates);
    } catch (err) {
      logger.error("Failed to fetch exchange rates:", err);
      setExchangeRates({});
    } finally {
      setIsLoadingRates(false);
    }
  };

  const refreshRates = async () => {
    await fetchExchangeRates();
  };

  useEffect(() => {
    fetchCurrencies();
  }, []);

  // Fetch exchange rates when user logs in or base_currency changes
  useEffect(() => {
    if (user?.base_currency) {
      fetchExchangeRates();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.base_currency]);

  const value: CurrencyContextType = {
    currencies,
    exchangeRates,
    isLoading,
    isLoadingRates,
    error,
    refreshCurrencies,
    refreshRates,
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = (): CurrencyContextType => {
  const context = useContext(CurrencyContext);
  if (context === undefined) {
    logger.error(
      "useCurrency: context is undefined, CurrencyProvider not found",
    );
    throw new Error("useCurrency must be used within a CurrencyProvider");
  }
  return context;
};
