import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  error = false,
  icon,
  className = '',
  ...props
}) => {
  const baseClasses = 'w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary';
  const errorClasses = error ? 'border-red-300 focus:ring-red-500' : '';
  const iconClasses = icon ? 'pl-10' : '';

  return (
    <div className="relative">
      {icon && (
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none theme-text-secondary">
          {icon}
        </div>
      )}
      <input
        className={`${baseClasses} ${errorClasses} ${iconClasses} ${className}`.trim()}
        {...props}
      />
    </div>
  );
};
