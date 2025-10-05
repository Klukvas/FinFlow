import React from 'react';
import { useCurrency } from '@/contexts/CurrencyContext';

interface CurrencySelectProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
  showFlags?: boolean;
}

export const CurrencySelect: React.FC<CurrencySelectProps> = ({
  value,
  onChange,
  disabled = false,
  className = '',
  placeholder = 'Выберите валюту',
  showFlags = true
}) => {
  const { currencies, isLoading, error } = useCurrency();

  const defaultClassName = "w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary disabled:opacity-50";
  const combinedClassName = `${defaultClassName} ${className}`;

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange(e.target.value);
  };

  if (error) {
    return (
      <select
        value={value}
        onChange={handleChange}
        disabled={disabled || true}
        className={combinedClassName}
      >
        <option value="USD">⚠️ USD - Ошибка загрузки валют</option>
      </select>
    );
  }

  return (
    <select
      value={value}
      onChange={handleChange}
      disabled={disabled || isLoading}
      className={combinedClassName}
    >
      {isLoading ? (
        <option disabled>🔄 Загрузка валют...</option>
      ) : currencies.length === 0 ? (
        <option value="USD">USD - Доллар США</option>
      ) : (
        <>
          <option value="" disabled>
            {placeholder}
          </option>
          {currencies.map((currency) => (
            <option key={currency.code} value={currency.code}>
              {showFlags ? `${currency.flag} ` : ''}{currency.code} - {currency.name}
            </option>
          ))}
        </>
      )}
    </select>
  );
};
