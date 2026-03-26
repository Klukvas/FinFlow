import React, { useEffect, useCallback, useRef, useId } from "react";
import { cn } from "@/utils/cn";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl" | "4xl" | "5xl" | "full";
  showCloseButton?: boolean;
  showHeader?: boolean;
  "data-testid"?: string;
}

const sizeClasses: Record<string, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  full: "max-w-[95vw]",
};

export const Modal = React.memo<ModalProps>(
  ({
    isOpen,
    onClose,
    title,
    subtitle,
    children,
    size = "md",
    showCloseButton = true,
    showHeader = true,
    "data-testid": testId,
  }) => {
    const modalRef = useRef<HTMLDivElement>(null);
    const titleId = useId();

    const handleKeyDown = useCallback(
      (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      },
      [onClose],
    );

    useEffect(() => {
      if (!isOpen) return;
      document.addEventListener("keydown", handleKeyDown);
      return () => {
        document.removeEventListener("keydown", handleKeyDown);
      };
    }, [isOpen, handleKeyDown]);

    useEffect(() => {
      if (!isOpen) return;
      document.body.style.overflow = "hidden";

      // Focus trap: move focus into modal on open
      const previouslyFocused = document.activeElement as HTMLElement | null;
      requestAnimationFrame(() => {
        modalRef.current?.focus();
      });

      return () => {
        document.body.style.overflow = "";
        // Restore focus on close
        previouslyFocused?.focus();
      };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
      <div
        className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center overflow-y-auto p-4"
        style={{
          backdropFilter: "blur(4px)",
          WebkitBackdropFilter: "blur(4px)",
        }}
      >
        {/* Overlay */}
        <div
          className="fixed inset-0 bg-[var(--bg-overlay)] animate-[fadeIn_0.15s_ease]"
          onClick={onClose}
          data-testid="modal-overlay"
        />

        {/* Modal body */}
        <div
          ref={modalRef}
          tabIndex={-1}
          className={cn(
            "relative w-full bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-xl)] p-7 animate-[slideUp_0.2s_ease] outline-none my-auto flex flex-col",
            "shadow-[var(--shadow-modal)] max-h-[calc(100vh-2rem)]",
            sizeClasses[size],
          )}
          data-testid={testId || "modal"}
          role="dialog"
          aria-modal="true"
          aria-labelledby={showHeader ? titleId : undefined}
        >
          {/* Close button */}
          {showCloseButton && (
            <button
              type="button"
              onClick={onClose}
              className="absolute top-5 right-5 w-7 h-7 rounded-[var(--radius-sm)] bg-transparent border-0 text-[var(--text-tertiary)] cursor-pointer flex items-center justify-center transition-all duration-100 hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)] min-h-[44px] min-w-[44px] touch-manipulation"
              aria-label="Close"
              data-testid="modal-close-button"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* Header */}
          {showHeader && (
            <div className="mb-6">
              <h2
                id={titleId}
                className="text-lg font-bold tracking-[-0.02em] text-[var(--text-primary)] pr-8"
                data-testid={testId ? `${testId}-title` : "modal-title"}
              >
                {title}
              </h2>
              {subtitle && (
                <p className="text-[13px] text-[var(--text-secondary)] mt-1">
                  {subtitle}
                </p>
              )}
            </div>
          )}

          {/* Content */}
          <div
            className="overflow-y-auto"
            data-testid={testId ? `${testId}-content` : "modal-content"}
          >
            {children}
          </div>
        </div>
      </div>
    );
  },
);

Modal.displayName = "Modal";

/* Utility sub-components for consistent modal layouts */
interface ModalSectionProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalBody: React.FC<ModalSectionProps> = ({
  children,
  className,
}) => <div className={cn("flex flex-col gap-4", className)}>{children}</div>;

export const ModalFooter: React.FC<ModalSectionProps> = ({
  children,
  className,
}) => (
  <div
    className={cn(
      "flex items-center justify-end gap-2.5 mt-6 pt-5 border-t border-[var(--border)]",
      className,
    )}
  >
    {children}
  </div>
);
