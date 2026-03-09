import React from "react";
import {
  Badge as BaseBadge,
  cn,
  type BadgeProps as BaseBadgeProps,
} from "@klukvas/flux-b2c-ui";

type Variant =
  | "default"
  | "secondary"
  | "destructive"
  | "outline"
  | "success"
  | "warning"
  | "info";

interface BadgeProps extends Omit<BaseBadgeProps, "variant"> {
  variant?: Variant;
  "data-testid"?: string;
}

const variantMap: Record<
  Variant,
  "secondary" | "destructive" | "outline" | "success"
> = {
  default: "secondary",
  secondary: "secondary",
  destructive: "destructive",
  outline: "outline",
  success: "success",
  warning: "secondary",
  info: "secondary",
};

const extraClasses: Partial<Record<Variant, string>> = {
  warning: "bg-[var(--color-warning-light)] text-[var(--color-warning)]",
  info: "bg-[var(--color-accent-light)] text-[var(--color-accent)]",
  default: "bg-[var(--color-accent-light)] text-[var(--color-accent)]",
};

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  (
    { variant = "default", className = "", "data-testid": testId, ...props },
    ref,
  ) => (
    <BaseBadge
      ref={ref}
      variant={variantMap[variant]}
      className={cn(extraClasses[variant], className)}
      data-testid={testId}
      {...props}
    />
  ),
);

Badge.displayName = "Badge";
