import React from 'react';
import { FaEdit } from 'react-icons/fa';

interface EditButtonProps {
  onEdit: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'filled' | 'icon';
  size?: 'sm' | 'md';
  className?: string;
  title?: string;
  dataTestId?: string;
}

export const EditButton: React.FC<EditButtonProps> = ({
  onEdit,
  disabled = false,
  loading = false,
  variant = 'icon',
  size = 'md',
  className = '',
  title = 'Редактировать',
  dataTestId = 'edit-button'
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    filled: 'px-3 py-1.5 border border-transparent text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
    icon: 'p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors'
  };
  
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`.trim();

  return (
    <button
      onClick={onEdit}
      disabled={disabled || loading}
      className={classes}
      title={title}
      data-testid={dataTestId}
    >
      {loading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Редактирование...
        </>
      ) : (
        <>
          <FaEdit className={`${variant === 'filled' ? 'w-3 h-3 mr-1' : 'w-4 h-4'}`} />
          {variant === 'filled' && 'Редактировать'}
        </>
      )}
    </button>
  );
};
