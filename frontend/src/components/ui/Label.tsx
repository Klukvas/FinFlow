import React from 'react';

interface LabelProps {
  children: React.ReactNode;
  htmlFor?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
  'data-testid'?: string;
}

export const Label: React.FC<LabelProps> = ({ 
  children, 
  htmlFor, 
  className = '',
  required = false,
  disabled = false,
  'data-testid': testId
}) => {
  return (
    <label 
      htmlFor={htmlFor}
      className={`block text-sm font-medium leading-none theme-text-primary transition-colors ${
        disabled ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'
      } ${className}`}
      data-testid={testId || 'label'}
    >
      {children}
      {required && <span className="text-red-500 ml-1" data-testid={testId ? `${testId}-required` : 'label-required'}>*</span>}
    </label>
  );
};
