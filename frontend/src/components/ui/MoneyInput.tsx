import React, { forwardRef } from 'react';

export interface MoneyInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'onChange'> {
  value?: string | number;
  onChange?: (value: string) => void;
  placeholder?: string;
  error?: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  currency?: string;
  'data-testid'?: string;
}

const MoneyInput = forwardRef<HTMLInputElement, MoneyInputProps>(
  ({ 
    value = '', 
    onChange, 
    placeholder = '0.00', 
    error, 
    label,
    required = false,
    disabled = false,
    className,
    currency = '$',
    'data-testid': testId,
    ...props 
  }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value;
      
      // Allow empty string, numbers, and decimal point
      if (inputValue === '' || /^\d*\.?\d*$/.test(inputValue)) {
        // Limit to 2 decimal places
        const parts = inputValue.split('.');
        if (parts.length === 2 && parts[1] && parts[1].length > 2) {
          return; // Don't update if more than 2 decimal places
        }
        
        // Limit to reasonable amount (999,999.99)
        const numValue = parseFloat(inputValue);
        if (numValue > 999999.99) {
          return; // Don't update if amount is too large
        }
        
        if (onChange) {
          onChange(inputValue);
        }
      }
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      // Format to 2 decimal places on blur if it's a valid number
      const inputValue = e.target.value;
      if (inputValue && !isNaN(parseFloat(inputValue))) {
        const formattedValue = parseFloat(inputValue).toFixed(2);
        if (onChange) {
          onChange(formattedValue);
        }
      }
    };

    return (
      <div className="space-y-2" data-testid={testId ? `${testId}-container` : 'money-input-container'}>
        {label && (
          <label 
            className="block text-sm font-medium theme-text-primary"
            data-testid={testId ? `${testId}-label` : 'money-input-label'}
          >
            {label}
            {required && <span className="text-red-500 ml-1" data-testid={testId ? `${testId}-required` : 'money-input-required'}>*</span>}
          </label>
        )}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span 
              className="theme-text-secondary text-sm font-medium"
              data-testid={testId ? `${testId}-currency` : 'money-input-currency'}
            >
              {currency}
            </span>
          </div>
          <input
            ref={ref}
            type="text"
            inputMode="decimal"
            value={value}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            data-testid={testId || 'money-input'}
            className={`block w-full pl-8 pr-3 py-3 text-base theme-border border rounded-lg shadow-sm theme-bg theme-text-primary placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition ${
              error ? "border-red-500 focus:ring-red-500 focus:border-red-500" : ""
            } ${
              disabled ? "theme-bg-tertiary cursor-not-allowed opacity-50" : "hover:theme-border-hover"
            } ${className || ""}`}
            {...props}
          />
        </div>
        {error && (
          <p 
            className="text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
            data-testid={testId ? `${testId}-error` : 'money-input-error'}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        )}
      </div>
    );
  }
);

MoneyInput.displayName = 'MoneyInput';

export { MoneyInput };
