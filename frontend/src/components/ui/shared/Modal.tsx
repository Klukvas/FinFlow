import React, { useEffect } from 'react';
import { FaTimes } from 'react-icons/fa';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';
  showCloseButton?: boolean;
  'data-testid'?: string;
}

export const Modal = React.memo<ModalProps>(({
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
    sm: 'max-w-sm mx-4',
    md: 'max-w-md mx-4',
    lg: 'max-w-lg mx-4',
    xl: 'max-w-xl mx-4',
    '2xl': 'max-w-2xl mx-4',
    '3xl': 'max-w-3xl mx-4',
    '4xl': 'max-w-4xl mx-4',
    '5xl': 'max-w-5xl mx-4',
    'full': 'max-w-[95vw] mx-4',
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
            className="flex items-center justify-between theme-border border-b px-4 sm:px-6 py-3 sm:py-4"
            data-testid={testId ? `${testId}-header` : 'modal-header'}
          >
            <h3 
              className="text-base sm:text-lg font-semibold theme-text-primary truncate pr-2"
              data-testid={testId ? `${testId}-title` : 'modal-title'}
            >
              {title}
            </h3>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="rounded-md p-2 theme-text-tertiary hover:theme-surface-hover hover:theme-text-primary theme-transition touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center flex-shrink-0"
                aria-label="Закрыть"
                data-testid='modal-close-button'
              >
                <FaTimes className="w-5 h-5" />
              </button>
            )}
          </div>
          
          {/* Content */}
          <div 
            className="px-4 sm:px-6 py-4 max-h-[70vh] sm:max-h-[80vh] overflow-y-auto"
            data-testid={testId ? `${testId}-content` : 'modal-content'}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
});
