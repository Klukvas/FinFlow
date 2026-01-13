import { ApiError } from '@/types';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export class HttpClient {
  private baseUrl: string;
  private getToken: () => string | null;
  private onUnauthorized?: () => void;

  constructor(
    baseUrl: string,
    getToken: () => string | null,
    onUnauthorized?: () => void
  ) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
    this.onUnauthorized = onUnauthorized;
  }

  private async request<T>(
    method: HttpMethod,
    endpoint: string,
    data?: unknown
  ): Promise<T | ApiError> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });

      if (response.status === 401) {
        this.onUnauthorized?.();
        return { error: 'Unauthorized', status: 401 };
      }

      if (response.status === 403) {
        return { error: 'Access denied. Admin privileges required.', status: 403 };
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error: errorData.detail || errorData.error || `HTTP ${response.status}`,
          status: response.status,
        };
      }

      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      console.error('Request failed:', error);
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  get<T>(endpoint: string): Promise<T | ApiError> {
    return this.request<T>('GET', endpoint);
  }

  post<T>(endpoint: string, data?: unknown): Promise<T | ApiError> {
    return this.request<T>('POST', endpoint, data);
  }

  put<T>(endpoint: string, data?: unknown): Promise<T | ApiError> {
    return this.request<T>('PUT', endpoint, data);
  }

  patch<T>(endpoint: string, data?: unknown): Promise<T | ApiError> {
    return this.request<T>('PATCH', endpoint, data);
  }

  delete<T>(endpoint: string): Promise<T | ApiError> {
    return this.request<T>('DELETE', endpoint);
  }
}
