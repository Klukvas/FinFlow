import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  'data-testid'?: string;
}

export const Button = React.memo<ButtonProps>(({
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
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg theme-transition focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-[var(--color-accent)] disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation';

  const variantClasses = {
    primary: 'theme-accent-bg text-white hover:theme-accent-hover',
    secondary: 'theme-surface theme-text-primary hover:theme-surface-hover border theme-border',
    danger: 'theme-error-bg text-white hover:bg-red-700',
    outline: 'border theme-border theme-text-primary hover:theme-surface-hover bg-transparent',
    ghost: 'theme-text-primary hover:theme-surface-hover bg-transparent',
    link: 'theme-accent bg-transparent hover:underline underline-offset-4',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-2.5 text-sm min-h-[44px]',
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
});
