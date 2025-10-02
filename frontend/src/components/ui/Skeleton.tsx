import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
  'data-testid'?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
  'data-testid': testId
}) => {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';
  
  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded'
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-pulse',
    none: ''
  };

  const style = {
    width: width ? (typeof width === 'number' ? `${width}px` : width) : undefined,
    height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined,
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${animationClasses[animation]} ${className}`}
      style={style}
      data-testid={testId || `skeleton-${variant}`}
    />
  );
};

// Predefined skeleton components for common use cases
export const SkeletonText: React.FC<{ lines?: number; className?: string; 'data-testid'?: string }> = ({ 
  lines = 1, 
  className = '',
  'data-testid': testId
}) => (
  <div 
    className={`space-y-2 ${className}`}
    data-testid={testId || 'skeleton-text'}
  >
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} variant="text" className="h-4" data-testid={testId ? `${testId}-line-${i}` : `skeleton-text-line-${i}`} />
    ))}
  </div>
);

export const SkeletonCard: React.FC<{ className?: string; 'data-testid'?: string }> = ({ className = '', 'data-testid': testId }) => (
  <div 
    className={`p-6 space-y-4 ${className}`}
    data-testid={testId || 'skeleton-card'}
  >
    <div className="flex items-center space-x-4">
      <Skeleton variant="circular" width={40} height={40} data-testid={testId ? `${testId}-avatar` : 'skeleton-card-avatar'} />
      <div className="space-y-2 flex-1">
        <Skeleton variant="text" className="h-4 w-3/4" data-testid={testId ? `${testId}-title` : 'skeleton-card-title'} />
        <Skeleton variant="text" className="h-4 w-1/2" data-testid={testId ? `${testId}-subtitle` : 'skeleton-card-subtitle'} />
      </div>
    </div>
    <Skeleton variant="text" className="h-4" data-testid={testId ? `${testId}-line1` : 'skeleton-card-line1'} />
    <Skeleton variant="text" className="h-4 w-5/6" data-testid={testId ? `${testId}-line2` : 'skeleton-card-line2'} />
  </div>
);

export const SkeletonTable: React.FC<{ 
  rows?: number; 
  columns?: number; 
  className?: string;
  'data-testid'?: string;
}> = ({ rows = 5, columns = 4, className = '', 'data-testid': testId }) => (
  <div 
    className={`space-y-3 ${className}`}
    data-testid={testId || 'skeleton-table'}
  >
    {/* Header */}
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={`header-${i}`} variant="text" className="h-5" data-testid={testId ? `${testId}-header-${i}` : `skeleton-table-header-${i}`} />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton key={`row-${rowIndex}-col-${colIndex}`} variant="text" className="h-4" data-testid={testId ? `${testId}-row-${rowIndex}-col-${colIndex}` : `skeleton-table-row-${rowIndex}-col-${colIndex}`} />
        ))}
      </div>
    ))}
  </div>
);
