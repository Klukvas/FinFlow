import React from "react";
import {
  Skeleton as BaseSkeleton,
  SkeletonText as BaseSkeletonText,
  SkeletonCard as BaseSkeletonCard,
} from "@klukvas/flux-b2c-ui";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animation?: "pulse" | "none";
  "data-testid"?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  animation = "pulse",
  "data-testid": testId,
  ...props
}) => (
  <BaseSkeleton
    animation={animation}
    data-testid={testId || `skeleton-${props.variant || "rectangular"}`}
    {...props}
  />
);

export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
  "data-testid"?: string;
}> = ({ "data-testid": testId, ...props }) => (
  <BaseSkeletonText data-testid={testId || "skeleton-text"} {...props} />
);

export const SkeletonCard: React.FC<{
  className?: string;
  "data-testid"?: string;
}> = ({ "data-testid": testId, ...props }) => (
  <BaseSkeletonCard data-testid={testId || "skeleton-card"} {...props} />
);

export const SkeletonTable: React.FC<{
  rows?: number;
  columns?: number;
  className?: string;
  "data-testid"?: string;
}> = ({ rows = 5, columns = 4, className = "", "data-testid": testId }) => (
  <div
    className={`space-y-3 ${className}`}
    data-testid={testId || "skeleton-table"}
  >
    <div
      className="grid gap-4"
      style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
    >
      {Array.from({ length: columns }).map((_, i) => (
        <BaseSkeleton key={`header-${i}`} variant="text" className="h-5" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div
        key={rowIndex}
        className="grid gap-4"
        style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
      >
        {Array.from({ length: columns }).map((_, colIndex) => (
          <BaseSkeleton
            key={`row-${rowIndex}-col-${colIndex}`}
            variant="text"
            className="h-4"
          />
        ))}
      </div>
    ))}
  </div>
);
