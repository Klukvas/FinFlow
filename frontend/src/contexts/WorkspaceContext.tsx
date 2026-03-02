import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
  useMemo,
} from "react";
import {
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
  WorkspaceListResponse,
} from "@/types";
import { WorkspaceApiClient } from "@/services/api/workspaceApiClient";
import { useAuth } from "./AuthContext";
import {
  getStoredWorkspaceId,
  setStoredWorkspaceId,
} from "@/utils/workspaceStorage";
import { logger } from "@/utils/logger";

interface WorkspaceContextType {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  currentWorkspaceId: string | null;
  isLoading: boolean;
  error: string | null;
  // Actions
  setCurrentWorkspace: (workspaceId: string) => void;
  refreshWorkspaces: () => Promise<void>;
  createWorkspace: (data: WorkspaceCreate) => Promise<Workspace | null>;
  updateWorkspace: (
    workspaceId: string,
    data: WorkspaceUpdate,
  ) => Promise<Workspace | null>;
  archiveWorkspace: (workspaceId: string) => Promise<boolean>;
  unarchiveWorkspace: (workspaceId: string) => Promise<boolean>;
  leaveWorkspace: (workspaceId: string) => Promise<boolean>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(
  undefined,
);

interface WorkspaceProviderProps {
  children: ReactNode;
}

export const WorkspaceProvider: React.FC<WorkspaceProviderProps> = ({
  children,
}) => {
  const { token, isAuthenticated, refreshAccessToken } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(
    () => getStoredWorkspaceId(),
  );
  const [isLoading, setIsLoading] = useState(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create API client
  const workspaceApi = useMemo(() => {
    const getToken = () => token;
    const refreshTokenFn = () => refreshAccessToken();
    return new WorkspaceApiClient(getToken, refreshTokenFn);
  }, [token, refreshAccessToken]);

  // Find current workspace from list
  const currentWorkspace = useMemo(() => {
    if (!currentWorkspaceId) return null;
    return workspaces.find((w) => w.id === currentWorkspaceId) || null;
  }, [workspaces, currentWorkspaceId]);

  // Fetch workspaces
  const refreshWorkspaces = useCallback(async () => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await workspaceApi.getWorkspaces();

      if ("error" in response) {
        setError(response.error);
        return;
      }

      let workspaceList = (response as WorkspaceListResponse).workspaces || [];

      // If no workspaces exist, try to create a personal workspace
      // This handles the case where backend workspace creation failed during registration
      if (workspaceList.length === 0) {
        logger.info(
          "[WorkspaceContext] No workspaces found, creating personal workspace...",
        );
        const createResponse = await workspaceApi.createWorkspace({
          name: "Personal",
          type: "personal",
        });
        if (!("error" in createResponse)) {
          const newWorkspace = createResponse as Workspace;
          workspaceList = [newWorkspace];
          logger.info(
            "[WorkspaceContext] Personal workspace created:",
            newWorkspace.id,
          );
        } else {
          logger.error(
            "[WorkspaceContext] Failed to create personal workspace:",
            createResponse.error,
          );
        }
      }

      setWorkspaces(workspaceList);

      // Get the stored workspace ID from localStorage
      const storedId = getStoredWorkspaceId();

      // Check if stored workspace exists in the list
      const storedWorkspaceExists =
        storedId && workspaceList.some((w) => w.id === storedId);

      if (storedWorkspaceExists) {
        // If stored workspace exists, make sure React state matches localStorage
        setCurrentWorkspaceId(storedId);
      } else if (workspaceList.length > 0) {
        // If no valid stored workspace, set default (personal or first)
        const personalWorkspace = workspaceList.find(
          (w) => w.type === "personal",
        );
        const defaultWorkspace = personalWorkspace ?? workspaceList[0];
        if (defaultWorkspace) {
          setCurrentWorkspaceId(defaultWorkspace.id);
          setStoredWorkspaceId(defaultWorkspace.id);
        }
      }
    } catch (err) {
      logger.error("Failed to fetch workspaces:", err);
      setError("Failed to load workspaces");
    } finally {
      setIsLoading(false);
      setHasInitiallyLoaded(true);
    }
  }, [isAuthenticated, workspaceApi]);

  // Set current workspace
  const setCurrentWorkspace = useCallback((workspaceId: string) => {
    setCurrentWorkspaceId(workspaceId);
    setStoredWorkspaceId(workspaceId);
  }, []);

  // Create workspace
  const createWorkspace = useCallback(
    async (data: WorkspaceCreate): Promise<Workspace | null> => {
      setError(null);
      try {
        const response = await workspaceApi.createWorkspace(data);

        if ("error" in response) {
          setError(response.error);
          return null;
        }

        const newWorkspace = response as Workspace;
        setWorkspaces((prev) => [...prev, newWorkspace]);
        return newWorkspace;
      } catch (err) {
        logger.error("Failed to create workspace:", err);
        setError("Failed to create workspace");
        return null;
      }
    },
    [workspaceApi],
  );

  // Update workspace
  const updateWorkspace = useCallback(
    async (
      workspaceId: string,
      data: WorkspaceUpdate,
    ): Promise<Workspace | null> => {
      setError(null);
      try {
        const response = await workspaceApi.updateWorkspace(workspaceId, data);

        if ("error" in response) {
          setError(response.error);
          return null;
        }

        const updatedWorkspace = response as Workspace;
        setWorkspaces((prev) =>
          prev.map((w) => (w.id === workspaceId ? updatedWorkspace : w)),
        );
        return updatedWorkspace;
      } catch (err) {
        logger.error("Failed to update workspace:", err);
        setError("Failed to update workspace");
        return null;
      }
    },
    [workspaceApi],
  );

  // Archive workspace
  const archiveWorkspace = useCallback(
    async (workspaceId: string): Promise<boolean> => {
      setError(null);
      try {
        const response = await workspaceApi.archiveWorkspace(workspaceId);

        if ("error" in response) {
          setError(response.error);
          return false;
        }

        // Remove from active workspaces list
        setWorkspaces((prev) => prev.filter((w) => w.id !== workspaceId));

        // If archived workspace was current, switch to another
        if (currentWorkspaceId === workspaceId) {
          const remaining = workspaces.filter((w) => w.id !== workspaceId);
          if (remaining.length > 0) {
            const personalWorkspace = remaining.find(
              (w) => w.type === "personal",
            );
            const newCurrent = personalWorkspace ?? remaining[0];
            if (newCurrent) setCurrentWorkspace(newCurrent.id);
          } else {
            setCurrentWorkspaceId(null);
            setStoredWorkspaceId(null);
          }
        }

        return true;
      } catch (err) {
        logger.error("Failed to archive workspace:", err);
        setError("Failed to archive workspace");
        return false;
      }
    },
    [workspaceApi, currentWorkspaceId, workspaces, setCurrentWorkspace],
  );

  // Unarchive workspace
  const unarchiveWorkspace = useCallback(
    async (workspaceId: string): Promise<boolean> => {
      setError(null);
      try {
        const response = await workspaceApi.unarchiveWorkspace(workspaceId);

        if ("error" in response) {
          setError(response.error);
          return false;
        }

        await refreshWorkspaces();
        return true;
      } catch (err) {
        logger.error("Failed to unarchive workspace:", err);
        setError("Failed to unarchive workspace");
        return false;
      }
    },
    [workspaceApi, refreshWorkspaces],
  );

  // Leave workspace
  const leaveWorkspace = useCallback(
    async (workspaceId: string): Promise<boolean> => {
      setError(null);
      try {
        const response = await workspaceApi.leaveWorkspace(workspaceId);

        if (response && "error" in response) {
          setError(response.error);
          return false;
        }

        // Remove from workspaces list
        setWorkspaces((prev) => prev.filter((w) => w.id !== workspaceId));

        // If left workspace was current, switch to another
        if (currentWorkspaceId === workspaceId) {
          const remaining = workspaces.filter((w) => w.id !== workspaceId);
          if (remaining.length > 0) {
            const personalWorkspace = remaining.find(
              (w) => w.type === "personal",
            );
            const newCurrent = personalWorkspace ?? remaining[0];
            if (newCurrent) setCurrentWorkspace(newCurrent.id);
          }
        }

        return true;
      } catch (err) {
        logger.error("Failed to leave workspace:", err);
        setError("Failed to leave workspace");
        return false;
      }
    },
    [workspaceApi, currentWorkspaceId, workspaces, setCurrentWorkspace],
  );

  // Load workspaces on auth change
  useEffect(() => {
    if (isAuthenticated) {
      refreshWorkspaces();
    } else {
      // Reset on logout so next login shows loading until workspaces are fetched
      setHasInitiallyLoaded(false);
    }
  }, [isAuthenticated, refreshWorkspaces]);

  const value: WorkspaceContextType = {
    workspaces,
    currentWorkspace,
    currentWorkspaceId,
    // Report loading=true during the gap between isAuthenticated becoming true
    // and refreshWorkspaces() actually starting (covers the useEffect delay)
    isLoading: isLoading || (isAuthenticated && !hasInitiallyLoaded),
    error,
    setCurrentWorkspace,
    refreshWorkspaces,
    createWorkspace,
    updateWorkspace,
    archiveWorkspace,
    unarchiveWorkspace,
    leaveWorkspace,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = (): WorkspaceContextType => {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
};
