import React from "react";
import { cn } from "@/utils/cn";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "outline" | "ghost" | "link";
  size?: "sm" | "md" | "lg" | "xl";
  fullWidth?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  "data-testid"?: string;
}

const variantStyles: Record<string, string> = {
  primary:
    "bg-[var(--accent)] text-[var(--accent-text)] hover:bg-[var(--accent-hover)] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(34,217,160,0.25)] active:scale-[0.98]",
  secondary:
    "bg-[var(--bg-raised)] text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border-hover)]",
  danger:
    "bg-[var(--danger-dim)] text-[var(--danger)] border border-[var(--danger-border)] hover:bg-[rgba(248,113,113,0.18)]",
  outline:
    "bg-transparent text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border-hover)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)]",
  ghost:
    "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)]",
  link:
    "bg-transparent text-[var(--accent)] underline-offset-2 hover:underline p-0 h-auto min-h-0",
};

const sizeStyles: Record<string, string> = {
  sm: "min-h-[36px] px-3 py-1.5 text-xs rounded-[var(--radius-sm)]",
  md: "min-h-[44px] px-4 py-2 text-sm rounded-[var(--radius-md)]",
  lg: "min-h-[48px] px-6 py-3 text-[15px] rounded-[var(--radius-md)]",
  xl: "min-h-[56px] px-7 py-3.5 text-base rounded-[var(--radius-md)]",
};

export const Button = React.memo(
  React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
      {
        variant = "primary",
        size = "md",
        fullWidth = false,
        loading = false,
        children,
        className = "",
        disabled,
        "data-testid": testId,
        ...props
      },
      ref,
    ) => (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 font-semibold border-0 cursor-pointer transition-all duration-150 whitespace-nowrap touch-manipulation",
          "disabled:opacity-40 disabled:pointer-events-none",
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && "w-full",
          className,
        )}
        disabled={disabled || loading}
        data-testid={testId}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 flex-shrink-0"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
        )}
        {children}
      </button>
    ),
  ),
);

Button.displayName = "Button";
