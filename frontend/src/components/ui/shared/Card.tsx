import React from "react";
import {
  Card as BaseCard,
  CardHeader as BaseCardHeader,
  CardTitle as BaseCardTitle,
  CardContent as BaseCardContent,
  CardFooter as BaseCardFooter,
  cn,
} from "@klukvas/flux-b2c-ui";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  "data-testid"?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", hover = false, "data-testid": testId, ...props }, ref) => (
    <BaseCard
      ref={ref}
      className={cn(
        "rounded-xl",
        hover &&
          "hover:border-[var(--color-border-hover)] hover:bg-[var(--color-surface-alt)]",
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
    <BaseCardHeader
      ref={ref}
      className={cn("p-4 pb-0 sm:p-6 sm:pb-0", className)}
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
  <BaseCardTitle
    ref={ref}
    className={cn("text-lg", className)}
    data-testid={testId || "card-title"}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

export const CardContent = React.forwardRef<HTMLDivElement, SubComponentProps>(
  ({ className = "", "data-testid": testId, ...props }, ref) => (
    <BaseCardContent
      ref={ref}
      className={cn("p-4 sm:p-6", className)}
      data-testid={testId || "card-content"}
      {...props}
    />
  ),
);
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<HTMLDivElement, SubComponentProps>(
  ({ className = "", "data-testid": testId, ...props }, ref) => (
    <BaseCardFooter
      ref={ref}
      className={cn(
        "border-t border-[var(--color-border)] p-4 pt-0 sm:p-6 sm:pt-0",
        className,
      )}
      data-testid={testId || "card-footer"}
      {...props}
    />
  ),
);
CardFooter.displayName = "CardFooter";
