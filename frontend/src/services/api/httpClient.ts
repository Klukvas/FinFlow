import { config } from '@/config/env';

const TOKEN_KEY = 'access_token';

export interface ApiError {
  error: string;
  status?: number;
  message?: string;
}

export class HttpClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string, timeout: number = 10000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  private getToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (error) {
      console.error('Failed to get token from localStorage:', error);
      return null;
    }
  }

  private async request<T>(
    method: string, 
    path: string, 
    data?: unknown
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const token = this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (config.debug) {
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : null,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (config.debug) {
      }

      if (!response.ok) {
        const errorData = await this.parseErrorResponse(response);
        throw errorData;
      }

      return await this.parseSuccessResponse<T>(response);
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw { error: 'Request timeout' };
      }
      
      throw error;
    }
  }

  private async parseErrorResponse(response: Response): Promise<ApiError> {
    try {
      const text = await response.text();
      let errorData: any = {};
      
      if (text) {
        try {
          errorData = JSON.parse(text);
        } catch (parseError) {
          // If JSON parsing fails, use the raw text
          errorData = { error: text };
        }
      }
      
      // If no error message in response, use a generic one based on status
      if (!errorData.error && !errorData.message) {
        errorData.error = this.getGenericErrorMessage(response.status);
      }
      
      if (config.debug) {
        console.error('Error response:', errorData);
      }
      
      return {
        ...errorData,
        status: response.status,
      };
    } catch (e) {
      console.error('Error parsing error response:', e);
      return { 
        error: this.getGenericErrorMessage(response.status),
        status: response.status,
      };
    }
  }

  private getGenericErrorMessage(status: number): string {
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

    return statusMessages[status] || `Ошибка сервера (${status})`;
  }

  private async parseSuccessResponse<T>(response: Response): Promise<T> {
    try {
      const text = await response.text();
      
      if (!text) {
        throw new Error('Empty response from server');
      }
      
      if (config.debug) {
      }
      
      return JSON.parse(text);
    } catch (e) {
      console.error('Error parsing success response:', e);
      throw { error: 'Invalid JSON response' };
    }
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('POST', path, data);
  }

  async put<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('PUT', path, data);
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }

  async patch<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>('PATCH', path, data);
  }
}