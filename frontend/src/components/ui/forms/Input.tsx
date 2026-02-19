import React from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  error?: boolean;
  icon?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  'data-testid'?: string;
}

export const Input: React.FC<InputProps> = ({
  error = false,
  icon,
  size = 'md',
  className = '',
  'data-testid': testId,
  ...props
}) => {
  const sizeClasses = {
    sm: 'h-10 px-3 py-2 text-sm',
    md: 'h-12 px-4 py-3 text-base',
    lg: 'h-14 px-4 py-4 text-lg'
  };

  const baseClasses = `w-full ${sizeClasses[size]} theme-bg border theme-border rounded-lg theme-text-primary placeholder:theme-text-tertiary hover:theme-border-hover focus:outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]/40 theme-transition`;
  const errorClasses = error ? 'border-red-500/70 focus:border-red-500/70 focus:ring-red-500/40' : '';
  const iconClasses = icon ? 'pl-10' : '';

  return (
    <div className="relative w-full" data-testid={testId ? `${testId}-container` : 'input-container'}>
      {icon && (
        <div
          className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none opacity-60 z-10"
          data-testid={testId ? `${testId}-icon` : 'input-icon'}
        >
          {icon}
        </div>
      )}
      <input
        className={`${baseClasses} ${errorClasses} ${iconClasses} ${className}`.trim()}
        data-testid={testId || 'input'}
        {...props}
      />
    </div>
  );
};
