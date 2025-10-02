import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  variant?: 'primary' | 'secondary' | 'accent';
  text?: string;
  'data-testid'?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '',
  variant = 'primary',
  text,
  'data-testid': testId
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const variantClasses = {
    primary: 'border-gray-300 border-t-blue-600',
    secondary: 'theme-border border-t-theme-text-primary',
    accent: 'theme-border border-t-theme-accent'
  };

  return (
    <div 
      className="flex flex-col items-center justify-center gap-2"
      data-testid={testId ? `${testId}-container` : 'loading-spinner-container'}
    >
      <div 
        className={`animate-spin rounded-full border-2 ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
        data-testid={testId || 'loading-spinner'}
      />
      {text && (
        <p 
          className="text-sm theme-text-secondary animate-pulse"
          data-testid={testId ? `${testId}-text` : 'loading-spinner-text'}
        >
          {text}
        </p>
      )}
    </div>
  );
};
