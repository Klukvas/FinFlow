import { config } from "@/config/env";
import { getStoredWorkspaceId } from "@/utils/workspaceStorage";
import { logger } from "@/utils/logger";

export interface ApiError {
  error: string;
  status?: number;
  errorCode?: string;
}

export class AuthHttpClient {
  private baseUrl: string;
  private getToken: () => string | null;
  private refreshToken: () => Promise<boolean>;
  private skipWorkspaceHeader: boolean;

  constructor(
    baseUrl: string,
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
    skipWorkspaceHeader: boolean = false,
  ) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
    this.refreshToken = refreshToken;
    this.skipWorkspaceHeader = skipWorkspaceHeader;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T | ApiError> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    // Only set Content-Type for JSON data, not for FormData
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // Add X-Workspace-Id header if available and not skipped
    if (!this.skipWorkspaceHeader) {
      const workspaceId = getStoredWorkspaceId();
      if (workspaceId) {
        headers["X-Workspace-Id"] = workspaceId;
      }
    }

    try {
      let response = await fetch(url, {
        ...options,
        headers,
      });

      // If token expired, try to refresh
      if (response.status === 401 && token) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry the request with new token
          const newToken = this.getToken();
          if (newToken) {
            headers.Authorization = `Bearer ${newToken}`;
            response = await fetch(url, {
              ...options,
              headers,
            });
          }
        } else {
          // If refresh failed, throw a user-friendly error
          throw {
            error: "Сессия истекла. Пожалуйста, войдите в систему заново.",
            status: 401,
          };
        }
      }

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
        error: error instanceof Error ? error.message : "Network error",
      };
    }
  }

  async get<T>(endpoint: string): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, { method: "GET" });
  }

  async post<T>(
    endpoint: string,
    data?: any,
    customHeaders?: Record<string, string>,
  ): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, {
      method: "POST",
      body: data
        ? data instanceof FormData
          ? data
          : JSON.stringify(data)
        : null,
      headers: customHeaders,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : null,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : null,
    });
  }

  async delete<T>(endpoint: string): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, { method: "DELETE" });
  }

  async deleteWithBody<T>(endpoint: string, data: any): Promise<T | ApiError> {
    return this.makeRequest<T>(endpoint, {
      method: "DELETE",
      body: JSON.stringify(data),
    });
  }
}
