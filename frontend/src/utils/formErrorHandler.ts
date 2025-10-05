import { toast } from 'sonner';
import { ErrorHandler, ApiError } from './errorHandler';

export interface FormFieldError {
  field: string;
  message: string;
}

export class FormErrorHandler {
  static handleFormError(
    error: unknown, 
    fallbackMessage: string = 'Произошла ошибка при сохранении',
    setFieldErrors?: (errors: Record<string, string>) => void
  ): void {
    if (error && typeof error === 'object') {
      const apiError = error as ApiError;
      
      // Handle validation errors (422) with field-specific messages
      if (apiError.status === 422 && apiError.error) {
        try {
          const errorData = JSON.parse(apiError.error);
          if (errorData.detail && Array.isArray(errorData.detail)) {
            // Handle FastAPI validation errors
            const fieldErrors: Record<string, string> = {};
            errorData.detail.forEach((err: any) => {
              if (err.loc && err.loc.length > 1) {
                const field = err.loc[1];
                fieldErrors[field] = err.msg || 'Неверное значение';
              }
            });
            
            if (Object.keys(fieldErrors).length > 0) {
              if (setFieldErrors) {
                setFieldErrors(fieldErrors);
              }
              toast.error('Проверьте введенные данные');
              return;
            }
          }
        } catch (parseError) {
          // If parsing fails, fall back to regular error handling
        }
      }
      
      // Handle field-specific errors from API response
      if (apiError.error && typeof apiError.error === 'object') {
        const errorObj = apiError.error as any;
        if (errorObj.errors && typeof errorObj.errors === 'object') {
          const fieldErrors: Record<string, string> = {};
          Object.entries(errorObj.errors).forEach(([field, messages]) => {
            if (Array.isArray(messages)) {
              fieldErrors[field] = messages[0] as string;
            } else if (typeof messages === 'string') {
              fieldErrors[field] = messages;
            }
          });
          
          if (Object.keys(fieldErrors).length > 0) {
            if (setFieldErrors) {
              setFieldErrors(fieldErrors);
            }
            toast.error('Проверьте введенные данные');
            return;
          }
        }
      }
    }
    
    // Fall back to regular error handling
    ErrorHandler.handleApiError(error, fallbackMessage);
  }

  static clearFieldErrors(setFieldErrors: (errors: Record<string, string>) => void): void {
    setFieldErrors({});
  }

  static getFieldError(errors: Record<string, string>, field: string): string | undefined {
    return errors[field];
  }

  static hasFieldError(errors: Record<string, string>, field: string): boolean {
    return !!errors[field];
  }
}
