import React from "react";
import { Button as BaseButton, cn } from "@klukvas/flux-b2c-ui";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "outline" | "ghost" | "link";
  size?: "sm" | "md" | "lg" | "xl";
  fullWidth?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  "data-testid"?: string;
}

const sizeMap = {
  sm: "sm" as const,
  md: "default" as const,
  lg: "lg" as const,
  xl: "default" as const,
};

const sizeClasses = {
  sm: "min-h-[36px] text-sm",
  md: "min-h-[44px] text-sm",
  lg: "min-h-[48px] text-base",
  xl: "h-14 min-h-[56px] px-8 py-4 text-lg",
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
        "data-testid": testId,
        ...props
      },
      ref,
    ) => (
      <BaseButton
        ref={ref}
        variant={variant}
        size={sizeMap[size]}
        loading={loading}
        className={cn(
          sizeClasses[size],
          fullWidth && "w-full",
          "touch-manipulation",
          className,
        )}
        data-testid={testId}
        {...props}
      >
        {children}
      </BaseButton>
    ),
  ),
);

Button.displayName = "Button";
