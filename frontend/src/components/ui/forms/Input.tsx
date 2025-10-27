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
    md: 'h-12 px-3 py-3 text-base', // Improved mobile touch target
    lg: 'h-14 px-4 py-4 text-lg'
  };

  const baseClasses = `w-full ${sizeClasses[size]} theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary placeholder-gray-400 hover:theme-border-hover`;
  const errorClasses = error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : '';
  const iconClasses = icon ? 'pl-10' : '';

  return (
    <div className="relative w-full" data-testid={testId ? `${testId}-container` : 'input-container'}>
      {icon && (
        <div 
          className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none theme-text-secondary z-10"
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
