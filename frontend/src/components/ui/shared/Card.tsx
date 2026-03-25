import React from "react";
import { cn } from "@/utils/cn";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  "data-testid"?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", hover = false, "data-testid": testId, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-lg)] transition-[border-color] duration-150",
        hover && "hover:border-[var(--border-hover)]",
        className,
      )}
      data-testid={testId || "card"}
      {...props}
    />
  ),
);
Card.displayName = "Card";

interface SubComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  "data-testid"?: string;
}

export const CardHeader = React.forwardRef<HTMLDivElement, SubComponentProps>(
  ({ className = "", "data-testid": testId, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("p-5 pb-0 sm:p-6 sm:pb-0", className)}
      data-testid={testId || "card-header"}
      {...props}
    />
  ),
);
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement> & { "data-testid"?: string }
>(({ className = "", "data-testid": testId, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-base font-semibold tracking-[-0.01em] text-[var(--text-primary)]",
      className,
    )}
    data-testid={testId || "card-title"}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

export const CardContent = React.forwardRef<HTMLDivElement, SubComponentProps>(
  ({ className = "", "data-testid": testId, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("p-5 sm:p-6", className)}
      data-testid={testId || "card-content"}
      {...props}
    />
  ),
);
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<HTMLDivElement, SubComponentProps>(
  ({ className = "", "data-testid": testId, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "border-t border-[var(--border)] p-5 sm:p-6",
        className,
      )}
      data-testid={testId || "card-footer"}
      {...props}
    />
  ),
);
CardFooter.displayName = "CardFooter";
