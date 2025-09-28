import React from 'react';
import { FaTrash } from 'react-icons/fa';

interface DeleteButtonProps {
  onDelete: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'filled' | 'icon';
  size?: 'sm' | 'md';
  className?: string;
  title?: string;
}

export const DeleteButton: React.FC<DeleteButtonProps> = ({
  onDelete,
  disabled = false,
  loading = false,
  variant = 'filled',
  size = 'md',
  className = '',
  title = 'Удалить'
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    filled: 'px-3 py-1.5 border border-transparent text-white bg-red-600 hover:bg-red-700 focus:ring-red-500',
    icon: 'p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors'
  };
  
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`.trim();

  return (
    <button
      onClick={onDelete}
      disabled={disabled || loading}
      className={classes}
      title={title}
    >
      {loading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Удаление...
        </>
      ) : (
        <>
          <FaTrash className={`${variant === 'filled' ? 'w-3 h-3 mr-1' : 'w-4 h-4'}`} />
          {variant === 'filled' && 'Удалить'}
        </>
      )}
    </button>
  );
};
