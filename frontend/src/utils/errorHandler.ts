import { toast } from 'sonner';

export interface ApiError {
  error: string;
  status?: number;
  message?: string;
}

export class ErrorHandler {
  private static getErrorMessage(error: unknown, fallbackMessage: string = 'Произошла ошибка'): string {
    if (error && typeof error === 'object') {
      const apiError = error as ApiError;
      
      // If we have a status code, provide user-friendly messages
      if (apiError.status) {
        const statusMessage = this.getStatusMessage(apiError.status);
        if (statusMessage) {
          return statusMessage;
        }
      }
      
      // Use the error message from the API if available
      if (apiError.error) {
        return apiError.error;
      }
      
      if (apiError.message) {
        return apiError.message;
      }
    } else if (typeof error === 'string') {
      return error;
    }

    return fallbackMessage;
  }

  private static getStatusMessage(status: number): string | null {
    const statusMessages: Record<number, string> = {
      400: 'Неверные данные. Проверьте введенную информацию.',
      401: 'Сессия истекла. Пожалуйста, войдите в систему заново.',
      403: 'У вас нет прав для выполнения этого действия.',
      404: 'Запрашиваемый ресурс не найден.',
      409: 'Конфликт данных. Возможно, запись уже существует.',
      422: 'Ошибка валидации данных. Проверьте введенную информацию.',
      429: 'Слишком много запросов. Попробуйте позже.',
      500: 'Внутренняя ошибка сервера. Попробуйте позже.',
      502: 'Сервер временно недоступен. Попробуйте позже.',
      503: 'Сервис временно недоступен. Попробуйте позже.',
      504: 'Время ожидания истекло. Попробуйте позже.',
    };

    return statusMessages[status] || null;
  }

  static handleApiError(error: unknown, fallbackMessage: string = 'Произошла ошибка'): void {
    const errorMessage = this.getErrorMessage(error, fallbackMessage);

    console.error('API Error:', error);
    toast.error(errorMessage);
  }

  static handleAsyncError<T>(
    asyncFn: () => Promise<T>,
    errorMessage: string = 'Произошла ошибка'
  ): Promise<T | null> {
    return asyncFn().catch((error) => {
      this.handleApiError(error, errorMessage);
      return null;
    });
  }

  static isApiError(error: unknown): error is ApiError {
    return (
      error !== null &&
      typeof error === 'object' &&
      'error' in error &&
      typeof (error as ApiError).error === 'string'
    );
  }
}
