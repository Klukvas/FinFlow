import { useState, useEffect } from 'react';
import { CurrencyApiClient } from '@/services/api/currencyApiClient';
import { useAuth } from '@/contexts/AuthContext';
import { useCurrency } from '@/contexts/CurrencyContext';

interface UseCurrencyConversionReturn {
  userCurrency: string;
  exchangeRates: Record<string, number>;
  isLoadingRates: boolean;
  convertToUserCurrency: (amount: number, fromCurrency: string) => number | null;
  formatCurrency: (amount: number, currency?: string) => string;
}

export const useCurrencyConversion = (): UseCurrencyConversionReturn => {
  const { user } = useAuth();
  const { currencies } = useCurrency();
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({});
  const [isLoadingRates, setIsLoadingRates] = useState(true);
  
  const userCurrency = user?.base_currency || 'USD';

  // Fetch exchange rates
  useEffect(() => {
    const fetchRates = async () => {
      try {
        const currencyClient = new CurrencyApiClient();
        const response = await currencyClient.getCurrencyRates(userCurrency);
        setExchangeRates(response.rates);
      } catch (error) {
        console.error('Failed to fetch exchange rates:', error);
        // Set empty rates on error
        setExchangeRates({});
      } finally {
        setIsLoadingRates(false);
      }
    };

    if (userCurrency) {
      fetchRates();
    }
  }, [userCurrency]);

  // Convert account balance to user's base currency
  const convertToUserCurrency = (amount: number, fromCurrency: string): number | null => {
    if (fromCurrency === userCurrency) {
      return amount;
    }
    
    const rate = exchangeRates[fromCurrency];
    if (!rate) {
      // If no rate available, return null to indicate conversion is not possible
      console.warn(`Exchange rate not available for ${fromCurrency} -> ${userCurrency}`);
      return null;
    }
    
    return amount / rate;
  };

  // Get locale for currency from backend data
  const getLocaleForCurrency = (currency: string): string => {
    const currencyInfo = currencies.find(c => c.code === currency);
    return currencyInfo?.locale || 'en-US';
  };

  // Format currency with proper locale and symbol
  const formatCurrency = (amount: number, currency: string = userCurrency): string => {
    const locale = getLocaleForCurrency(currency);
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  return {
    userCurrency,
    exchangeRates,
    isLoadingRates,
    convertToUserCurrency,
    formatCurrency
  };
};

