import React from 'react';

interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
  helpText?: string;
  disabled?: boolean;
  'data-testid'?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  required = false,
  children,
  className = '',
  helpText,
  disabled = false,
  'data-testid': testId
}) => {
  return (
    <div 
      className={`space-y-2 ${className}`}
      data-testid={testId || 'form-field'}
    >
      <label 
        className={`block text-sm font-medium theme-text-primary ${
          disabled ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'
        }`}
        data-testid={testId ? `${testId}-label` : 'form-field-label'}
      >
        {label}
        {required && <span className="text-red-500 ml-1" data-testid={testId ? `${testId}-required` : 'form-field-required'}>*</span>}
      </label>
      <div data-testid={testId ? `${testId}-input` : 'form-field-input'}>
        {children}
      </div>
      {helpText && !error && (
        <p 
          className="text-sm theme-text-tertiary"
          data-testid={testId ? `${testId}-help` : 'form-field-help'}
        >
          {helpText}
        </p>
      )}
      {error && (
        <p 
          className="text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
          data-testid={testId ? `${testId}-error` : 'form-field-error'}
        >
          <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};
