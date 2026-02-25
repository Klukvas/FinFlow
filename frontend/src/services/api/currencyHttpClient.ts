import { config } from "@/config/env";
import { logger } from "@/utils/logger";

export interface ApiError {
  error: string;
  errorCode?: string;
  status?: number;
  message?: string;
}

export class CurrencyHttpClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = config.api.currencyServiceUrl;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T | ApiError> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultHeaders = {
      "Content-Type": "application/json",
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error:
            errorData.error ||
            errorData.detail ||
            errorData.message ||
            `HTTP ${response.status}`,
          status: response.status,
          errorCode: errorData.errorCode, // Preserve errorCode from backend
        };
      }

      // Handle empty responses
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      } else {
        return {} as T;
      }
    } catch (error) {
      logger.error("Request failed:", error);
      return {
        error: "Network error occurred",
        errorCode: "NETWORK_ERROR",
      };
    }
  }

  async get<T>(endpoint: string): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: any): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : null,
    });
  }
}
