import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  cn,
} from "@klukvas/flux-b2c-ui";
import { FaTimes } from "react-icons/fa";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
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
    children,
    size = "md",
    showCloseButton = true,
    showHeader = true,
    "data-testid": testId,
  }) => (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent
        className={cn(
          "rounded-2xl border-[var(--color-border)]",
          sizeClasses[size],
        )}
        data-testid={testId || "modal"}
      >
        {showHeader && (
          <DialogHeader className="flex-row items-center justify-between pb-0">
            <DialogTitle
              className="truncate pr-2 text-xl"
              data-testid={testId ? `${testId}-title` : "modal-title"}
            >
              {title}
            </DialogTitle>
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                className="flex min-h-[44px] min-w-[44px] flex-shrink-0 items-center justify-center rounded-lg p-2 text-[var(--color-text-tertiary)] transition-colors hover:bg-[var(--color-surface-alt)] hover:text-[var(--color-text-secondary)] touch-manipulation"
                aria-label="Close"
                data-testid="modal-close-button"
              >
                <FaTimes className="h-4 w-4" />
              </button>
            )}
          </DialogHeader>
        )}

        {!showHeader && showCloseButton && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 z-10 flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg p-2 text-[var(--color-text-tertiary)] transition-colors hover:bg-[var(--color-surface-alt)] hover:text-[var(--color-text-secondary)] touch-manipulation"
            aria-label="Close"
            data-testid="modal-close-button"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        )}

        <div data-testid={testId ? `${testId}-content` : "modal-content"}>
          {children}
        </div>
      </DialogContent>
    </Dialog>
  ),
);

Modal.displayName = "Modal";
