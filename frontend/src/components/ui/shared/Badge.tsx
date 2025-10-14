import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  'data-testid'?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'default', 
  size = 'md',
  className = '',
  'data-testid': testId
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-full font-medium theme-transition';
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm'
  };
  
  const variantClasses = {
    default: 'theme-accent-light theme-accent',
    secondary: 'theme-bg-tertiary theme-text-secondary',
    destructive: 'theme-error-light theme-error',
    outline: 'theme-border border theme-text-primary hover:theme-surface-hover',
    success: 'theme-success-light theme-success',
    warning: 'theme-warning-light theme-warning',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
  };

  return (
    <span 
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      data-testid={testId || `badge-${variant}`}
    >
      {children}
    </span>
  );
};
