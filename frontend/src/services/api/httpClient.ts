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
      console.log(`[${method}] ${url}`, { headers, data });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (config.debug) {
        console.log(`Response status: ${response.status}`);
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
      const errorData = text ? JSON.parse(text) : { error: `HTTP error ${response.status}` };
      
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
        error: `HTTP error ${response.status}`,
        status: response.status,
      };
    }
  }

  private async parseSuccessResponse<T>(response: Response): Promise<T> {
    try {
      const text = await response.text();
      
      if (!text) {
        throw new Error('Empty response from server');
      }
      
      if (config.debug) {
        console.log('Success response:', text);
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