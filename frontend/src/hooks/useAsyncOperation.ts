import { useState, useCallback } from 'react';
import { ErrorHandler } from '@/utils/errorHandler';

interface UseAsyncOperationOptions {
  onSuccess?: () => void;
  onError?: (error: unknown) => void;
  successMessage?: string;
  errorMessage?: string;
}

export const useAsyncOperation = (options: UseAsyncOperationOptions = {}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    customOptions?: Partial<UseAsyncOperationOptions>
  ): Promise<T | null> => {
    const { onSuccess, onError, successMessage, errorMessage } = { ...options, ...customOptions };
    
    setIsLoading(true);
    setError(null);

    try {
      const result = await asyncFn();
      
      if (successMessage) {
        // You can add toast notification here if needed
      }
      
      if (onSuccess) {
        onSuccess();
      }
      
      return result;
    } catch (err) {
      const finalErrorMessage = errorMessage || 'Произошла ошибка';
      setError(finalErrorMessage);
      
      if (onError) {
        onError(err);
      } else {
        ErrorHandler.handleApiError(err, finalErrorMessage);
      }
      
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    execute,
    clearError,
  };
};
