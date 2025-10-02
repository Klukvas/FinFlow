import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  'data-testid'?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  children,
  className = '',
  disabled,
  'data-testid': testId,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg theme-transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation';
  
  const variantClasses = {
    primary: 'theme-accent-bg theme-text-inverse hover:theme-accent-hover focus:ring-blue-500 shadow-sm hover:shadow-md',
    secondary: 'theme-bg-tertiary theme-text-primary hover:theme-surface-hover focus:ring-gray-500 border theme-border',
    danger: 'theme-error-bg theme-text-inverse hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-md',
    outline: 'theme-border border theme-text-primary hover:theme-surface-hover focus:ring-blue-500 bg-transparent',
    ghost: 'theme-text-primary hover:theme-surface-hover focus:ring-gray-500 bg-transparent',
    link: 'theme-text-primary hover:theme-accent focus:ring-blue-500 bg-transparent underline-offset-4 hover:underline',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-2.5 text-sm min-h-[44px]', // Improved mobile touch target
    lg: 'px-6 py-3 text-base min-h-[48px]',
    xl: 'px-8 py-4 text-lg min-h-[56px]',
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${widthClass} ${className}`.trim();

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      data-testid={testId || `button-${variant}`}
      {...props}
    >
      {loading && (
        <div 
          className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent mr-2"
          data-testid={testId ? `${testId}-loading` : `button-${variant}-loading`}
        />
      )}
      {children}
    </button>
  );
};