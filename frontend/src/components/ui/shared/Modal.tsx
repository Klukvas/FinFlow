import React, { useEffect, useRef } from 'react';
import { FaTimes } from 'react-icons/fa';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';
  showCloseButton?: boolean;
  showHeader?: boolean;
  'data-testid'?: string;
}

export const Modal = React.memo<ModalProps>(({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  showHeader = true,
  'data-testid': testId,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

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

  // Focus trap
  useEffect(() => {
    if (!isOpen || !contentRef.current) return;

    const focusable = contentRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    // Autofocus first input
    const firstInput = contentRef.current.querySelector<HTMLElement>('input');
    if (firstInput) {
      requestAnimationFrame(() => firstInput.focus());
    }

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      if (focusable.length === 0) return;

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleTab);
    return () => document.removeEventListener('keydown', handleTab);
  }, [isOpen]);

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
      role="dialog"
      aria-modal="true"
      aria-labelledby={testId ? `${testId}-title` : 'modal-title'}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        data-testid={testId ? `${testId}-backdrop` : 'modal-backdrop'}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4 sm:p-6">
        <div
          ref={contentRef}
          className={`relative w-full ${sizeClasses[size]} transform overflow-hidden rounded-2xl theme-surface border theme-border theme-shadow-hover transition-all duration-200 ease-out ${
            isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
          }`}
          onClick={(e) => e.stopPropagation()}
          data-testid={testId || 'modal'}
        >
          {/* Header */}
          {showHeader && (
            <div
              className="flex items-center justify-between px-6 pt-6 pb-0"
              data-testid={testId ? `${testId}-header` : 'modal-header'}
            >
              <h3
                id={testId ? `${testId}-title` : 'modal-title'}
                className="text-xl font-semibold theme-text-primary truncate pr-2"
                data-testid={testId ? `${testId}-title` : 'modal-title'}
              >
                {title}
              </h3>
              {showCloseButton && (
                <button
                  onClick={onClose}
                  className="rounded-lg p-2 theme-text-tertiary hover:theme-surface-hover hover:theme-text-secondary theme-transition touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center flex-shrink-0"
                  aria-label="Close"
                  data-testid='modal-close-button'
                >
                  <FaTimes className="w-4 h-4" />
                </button>
              )}
            </div>
          )}

          {/* Close button when no header */}
          {!showHeader && showCloseButton && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 rounded-lg p-2 theme-text-tertiary hover:theme-surface-hover hover:theme-text-secondary theme-transition touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center z-10"
              aria-label="Close"
              data-testid='modal-close-button'
            >
              <FaTimes className="w-4 h-4" />
            </button>
          )}

          {/* Content */}
          <div
            className="px-6 py-6 max-h-[70vh] sm:max-h-[80vh] overflow-y-auto"
            data-testid={testId ? `${testId}-content` : 'modal-content'}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
});
