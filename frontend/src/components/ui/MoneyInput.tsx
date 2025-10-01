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
      <div className="space-y-1">
        {label && (
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-500 dark:text-gray-400 text-sm">$</span>
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
            className={`block w-full pl-7 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white ${
              error ? "border-red-500 focus:ring-red-500 focus:border-red-500" : ""
            } ${
              disabled ? "bg-gray-100 dark:bg-gray-800 cursor-not-allowed" : ""
            } ${className || ""}`}
            {...props}
          />
        </div>
        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

MoneyInput.displayName = 'MoneyInput';

export { MoneyInput };
