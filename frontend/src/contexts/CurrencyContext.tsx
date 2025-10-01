import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CurrencyApiClient, CurrencyInfo } from '@/services/api/currencyApiClient';

interface CurrencyContextType {
  currencies: CurrencyInfo[];
  isLoading: boolean;
  error: string | null;
  refreshCurrencies: () => Promise<void>;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

interface CurrencyProviderProps {
  children: ReactNode;
}

export const CurrencyProvider: React.FC<CurrencyProviderProps> = ({ children }) => {
  const [currencies, setCurrencies] = useState<CurrencyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  console.log('CurrencyProvider: Initializing...');

  const fetchCurrencies = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const currencyClient = new CurrencyApiClient();
      const response = await currencyClient.getSupportedCurrencies();
      setCurrencies(response.currencies);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch currencies';
      setError(errorMessage);
      console.error('Failed to fetch currencies:', err);
      
      // Fallback to basic currencies if API fails
      setCurrencies([
        { code: 'USD', name: 'US Dollar', symbol: '$', flag: '🇺🇸' },
        { code: 'EUR', name: 'Euro', symbol: '€', flag: '🇪🇺' },
        { code: 'GBP', name: 'British Pound', symbol: '£', flag: '🇬🇧' },
        { code: 'JPY', name: 'Japanese Yen', symbol: '¥', flag: '🇯🇵' },
        { code: 'CHF', name: 'Swiss Franc', symbol: 'CHF', flag: '🇨🇭' },
        { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$', flag: '🇨🇦' },
        { code: 'AUD', name: 'Australian Dollar', symbol: 'A$', flag: '🇦🇺' },
        { code: 'CNY', name: 'Chinese Yuan', symbol: '¥', flag: '🇨🇳' },
        { code: 'UAH', name: 'Ukrainian Hryvnia', symbol: '₴', flag: '🇺🇦' },
        { code: 'RUB', name: 'Russian Ruble', symbol: '₽', flag: '🇷🇺' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCurrencies = async () => {
    await fetchCurrencies();
  };

  useEffect(() => {
    fetchCurrencies();
  }, []);

  const value: CurrencyContextType = {
    currencies,
    isLoading,
    error,
    refreshCurrencies
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = (): CurrencyContextType => {
  const context = useContext(CurrencyContext);
  console.log('useCurrency: context =', context);
  if (context === undefined) {
    console.error('useCurrency: context is undefined, CurrencyProvider not found');
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
};
