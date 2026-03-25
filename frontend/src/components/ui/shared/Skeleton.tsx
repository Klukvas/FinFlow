import React from "react";
import { cn } from "@/utils/cn";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animation?: "pulse" | "none";
  "data-testid"?: string;
}

const variantStyles: Record<string, string> = {
  text: "h-3.5 w-3/5 rounded-[var(--radius-sm)]",
  circular: "rounded-full",
  rectangular: "rounded-[var(--radius-md)]",
};

export const Skeleton: React.FC<SkeletonProps> = ({
  className = "",
  variant = "rectangular",
  width,
  height,
  animation = "pulse",
  "data-testid": testId,
}) => (
  <div
    className={cn(
      "skeleton-shimmer",
      animation === "none" && "!animation-none",
      variantStyles[variant],
      className,
    )}
    style={{ width, height }}
    data-testid={testId || `skeleton-${variant}`}
  />
);

export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
  "data-testid"?: string;
}> = ({ lines = 3, className = "", "data-testid": testId }) => (
  <div
    className={cn("space-y-2.5", className)}
    data-testid={testId || "skeleton-text"}
  >
    {Array.from({ length: lines }).map((_, i) => (
      <div
        key={i}
        className={cn(
          "skeleton-shimmer h-3.5 rounded-[var(--radius-sm)]",
          i === lines - 1 ? "w-2/5" : "w-full",
        )}
      />
    ))}
  </div>
);

export const SkeletonCard: React.FC<{
  className?: string;
  "data-testid"?: string;
}> = ({ className = "", "data-testid": testId }) => (
  <div
    className={cn(
      "bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-lg)] p-5",
      className,
    )}
    data-testid={testId || "skeleton-card"}
  >
    <Skeleton variant="text" className="h-5 w-2/5 mb-4" />
    <SkeletonText lines={3} />
  </div>
);

export const SkeletonTable: React.FC<{
  rows?: number;
  columns?: number;
  className?: string;
  "data-testid"?: string;
}> = ({ rows = 5, columns = 4, className = "", "data-testid": testId }) => (
  <div
    className={cn("space-y-3", className)}
    data-testid={testId || "skeleton-table"}
  >
    <div
      className="grid gap-4"
      style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
    >
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={`header-${i}`} variant="text" className="h-5 w-full" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div
        key={rowIndex}
        className="grid gap-4"
        style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
      >
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton
            key={`row-${rowIndex}-col-${colIndex}`}
            variant="text"
            className="h-4 w-full"
          />
        ))}
      </div>
    ))}
  </div>
);
