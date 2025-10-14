import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

interface LoadingStateProps {
  isLoading: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

export const LoadingState = React.memo<LoadingStateProps>(({
  isLoading,
  children,
  fallback,
  className = '',
  'data-testid': testId,
}) => {
  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center p-8 ${className}`}
        data-testid={testId ? `${testId}-loading` : 'loading-state'}
      >
        {fallback || (
          <div className="flex flex-col items-center gap-4">
            <LoadingSpinner size="lg" />
            <p className="theme-text-tertiary text-sm">Загрузка...</p>
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
});

LoadingState.displayName = 'LoadingState';
