import { logger } from "@/utils/logger";

const WORKSPACE_ID_KEY = "current_workspace_id";

/**
 * Get workspace ID from localStorage
 * Used by AuthHttpClient to add X-Workspace-Id header
 */
export const getStoredWorkspaceId = (): string | null => {
  try {
    return localStorage.getItem(WORKSPACE_ID_KEY);
  } catch {
    return null;
  }
};

/**
 * Set workspace ID in localStorage
 */
export const setStoredWorkspaceId = (workspaceId: string | null): void => {
  try {
    if (workspaceId) {
      localStorage.setItem(WORKSPACE_ID_KEY, workspaceId);
    } else {
      localStorage.removeItem(WORKSPACE_ID_KEY);
    }
  } catch {
    logger.error("Failed to store workspace ID");
  }
};

/**
 * Clear workspace ID from localStorage (used on logout)
 */
export const clearStoredWorkspaceId = (): void => {
  try {
    localStorage.removeItem(WORKSPACE_ID_KEY);
  } catch {
    logger.error("Failed to clear workspace ID");
  }
};
