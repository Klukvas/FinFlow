import {
  AnalysisResponse,
  AnalysisRequest,
  PromptBlockMetadata,
} from "@/types";
import { AuthHttpClient, ApiError } from "./AuthHttpClient";
import { config } from "@/config/env";
import { getStoredWorkspaceId } from "@/utils/workspaceStorage";
import { logger } from "@/utils/logger";

export interface AiApiError extends ApiError {
  retry_after?: number;
}

export class AiAssistantApiClient {
  private httpClient: AuthHttpClient;
  private getToken: () => string | null;
  private refreshToken: () => Promise<boolean>;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    this.getToken = getToken;
    this.refreshToken = refreshToken;
    this.httpClient = new AuthHttpClient(
      `${config.api.aiAssistantServiceUrl}/api/v1`,
      getToken,
      refreshToken,
    );
  }

  async getPrompts(): Promise<PromptBlockMetadata[] | ApiError> {
    return this.httpClient.get<PromptBlockMetadata[]>("/prompts");
  }

  async analyze(
    request: AnalysisRequest,
  ): Promise<AnalysisResponse | AiApiError> {
    const url = `${config.api.aiAssistantServiceUrl}/api/v1/analyze`;
    const token = this.getToken();
    const workspaceId = getStoredWorkspaceId();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (workspaceId) headers["X-Workspace-Id"] = workspaceId;

    try {
      let response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(request),
      });

      if (response.status === 401 && token) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          const newToken = this.getToken();
          if (newToken) {
            headers.Authorization = `Bearer ${newToken}`;
            response = await fetch(url, {
              method: "POST",
              headers,
              body: JSON.stringify(request),
            });
          }
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error: errorData.error || `HTTP ${response.status}`,
          status: response.status,
          errorCode: errorData.errorCode,
          retry_after: errorData.retry_after,
        };
      }

      return await response.json();
    } catch (err) {
      logger.error(
        "AI analysis request failed:",
        err instanceof Error ? err.message : String(err),
      );
      return { error: err instanceof Error ? err.message : "Network error" };
    }
  }

  async getLastResult(
    promptId: string,
    language: string,
  ): Promise<AnalysisResponse | null | ApiError> {
    return this.httpClient.get<AnalysisResponse | null>(
      `/results/${promptId}?language=${encodeURIComponent(language)}`,
    );
  }

  async getUsage(): Promise<AiUsageInfo | ApiError> {
    return this.httpClient.get<AiUsageInfo>("/usage");
  }
}

export interface AiUsageInfo {
  used: number;
  quota: number;
  remaining: number;
  resets_in: number;
}
