import React from "react";
import { cn } from "@/utils/cn";

type Variant =
  | "default"
  | "secondary"
  | "destructive"
  | "outline"
  | "success"
  | "warning"
  | "info"
  | "accent"
  | "purple"
  | "pro";

type Size = "sm" | "md";

interface BadgeProps extends Omit<
  React.HTMLAttributes<HTMLSpanElement>,
  "size"
> {
  variant?: Variant;
  size?: Size;
  withDot?: boolean;
  "data-testid"?: string;
}

const sizeStyles: Record<Size, string> = {
  sm: "text-[10px] py-0.5 px-1.5",
  md: "text-[11px] py-[3px] px-2",
};

const variantStyles: Record<Variant, string> = {
  default:
    "bg-[var(--accent-dim)] text-[var(--accent)] border-[var(--accent-border)]",
  secondary:
    "bg-[var(--bg-raised)] text-[var(--text-secondary)] border-[var(--border)]",
  destructive:
    "bg-[var(--danger-dim)] text-[var(--danger)] border-[var(--danger-border)]",
  outline: "bg-transparent text-[var(--text-secondary)] border-[var(--border)]",
  success:
    "bg-[var(--success-dim)] text-[var(--success)] border-[var(--success-border)]",
  warning:
    "bg-[var(--warning-dim)] text-[var(--warning)] border-[var(--warning-border)]",
  info: "bg-[var(--info-dim)] text-[var(--info)] border-[var(--info-border)]",
  accent:
    "bg-[var(--accent-dim)] text-[var(--accent)] border-[var(--accent-border)]",
  purple:
    "bg-[var(--purple-dim)] text-[var(--purple)] border-[var(--purple-border)]",
  pro: "bg-[var(--purple-dim)] text-[var(--purple)] border-[var(--purple-border)] text-[10px] py-0.5 px-1.5",
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      variant = "default",
      size = "md",
      withDot = false,
      className = "",
      children,
      "data-testid": testId,
      ...props
    },
    ref,
  ) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center gap-[5px] font-mono font-medium rounded-[5px] border whitespace-nowrap leading-relaxed",
        sizeStyles[size],
        variantStyles[variant],
        className,
      )}
      data-testid={testId}
      {...props}
    >
      {withDot && (
        <span className="w-[5px] h-[5px] rounded-full bg-current flex-shrink-0" />
      )}
      {children}
    </span>
  ),
);

Badge.displayName = "Badge";
