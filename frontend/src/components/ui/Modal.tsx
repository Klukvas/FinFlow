import React, { useEffect } from 'react';
import { FaTimes } from 'react-icons/fa';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
  'data-testid'?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  'data-testid': testId,
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      data-testid={testId ? `${testId}-container` : 'modal-container'}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        data-testid={testId ? `${testId}-backdrop` : 'modal-backdrop'}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4 sm:p-6">
        <div
          className={`relative w-full ${sizeClasses[size]} transform overflow-hidden rounded-lg theme-surface theme-shadow transition-all duration-300 ease-out ${
            isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
          }`}
          onClick={(e) => e.stopPropagation()}
          data-testid={testId || 'modal'}
        >
          {/* Header */}
          <div 
            className="flex items-center justify-between theme-border border-b px-4 sm:px-6 py-4"
            data-testid={testId ? `${testId}-header` : 'modal-header'}
          >
            <h3 
              className="text-lg font-semibold theme-text-primary"
              data-testid={testId ? `${testId}-title` : 'modal-title'}
            >
              {title}
            </h3>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="rounded-md p-2 theme-text-tertiary hover:theme-surface-hover hover:theme-text-primary theme-transition touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Закрыть"
                data-testid={testId ? `${testId}-close-button` : 'modal-close-button'}
              >
                <FaTimes className="w-5 h-5" />
              </button>
            )}
          </div>
          
          {/* Content */}
          <div 
            className="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto"
            data-testid={testId ? `${testId}-content` : 'modal-content'}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};
