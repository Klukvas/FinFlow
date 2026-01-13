import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode, useMemo } from 'react';
import { Workspace, WorkspaceCreate, WorkspaceUpdate, WorkspaceListResponse } from '@/types';
import { WorkspaceApiClient } from '@/services/api/workspaceApiClient';
import { useAuth } from './AuthContext';
import { getStoredWorkspaceId, setStoredWorkspaceId } from '@/utils/workspaceStorage';

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
  updateWorkspace: (workspaceId: string, data: WorkspaceUpdate) => Promise<Workspace | null>;
  archiveWorkspace: (workspaceId: string) => Promise<boolean>;
  unarchiveWorkspace: (workspaceId: string) => Promise<boolean>;
  leaveWorkspace: (workspaceId: string) => Promise<boolean>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

interface WorkspaceProviderProps {
  children: ReactNode;
}

export const WorkspaceProvider: React.FC<WorkspaceProviderProps> = ({ children }) => {
  const { token, isAuthenticated, refreshAccessToken } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(() => getStoredWorkspaceId());
  const [isLoading, setIsLoading] = useState(false);
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
    return workspaces.find(w => w.id === currentWorkspaceId) || null;
  }, [workspaces, currentWorkspaceId]);

  // Fetch workspaces
  const refreshWorkspaces = useCallback(async () => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await workspaceApi.getWorkspaces();
      
      if ('error' in response) {
        setError(response.error);
        return;
      }

      const workspaceList = (response as WorkspaceListResponse).workspaces;
      setWorkspaces(workspaceList);

      // Get the stored workspace ID from localStorage
      const storedId = getStoredWorkspaceId();
      
      console.log('[WorkspaceContext] Stored workspace ID:', storedId);
      console.log('[WorkspaceContext] Available workspaces:', workspaceList.map(w => ({ id: w.id, name: w.name })));
      
      // Check if stored workspace exists in the list
      const storedWorkspaceExists = storedId && workspaceList.some(w => w.id === storedId);
      console.log('[WorkspaceContext] Stored workspace exists in list:', storedWorkspaceExists);

      if (storedWorkspaceExists) {
        // If stored workspace exists, make sure React state matches localStorage
        console.log('[WorkspaceContext] Using stored workspace:', storedId);
        setCurrentWorkspaceId(storedId);
      } else if (workspaceList.length > 0) {
        // If no valid stored workspace, set default (personal or first)
        const personalWorkspace = workspaceList.find(w => w.type === 'personal');
        const defaultWorkspace = personalWorkspace || workspaceList[0];
        console.log('[WorkspaceContext] Stored workspace not found, defaulting to:', defaultWorkspace.id, defaultWorkspace.name);
        setCurrentWorkspaceId(defaultWorkspace.id);
        setStoredWorkspaceId(defaultWorkspace.id);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
      setError('Failed to load workspaces');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, workspaceApi]);

  // Set current workspace
  const setCurrentWorkspace = useCallback((workspaceId: string) => {
    setCurrentWorkspaceId(workspaceId);
    setStoredWorkspaceId(workspaceId);
  }, []);

  // Create workspace
  const createWorkspace = useCallback(async (data: WorkspaceCreate): Promise<Workspace | null> => {
    setError(null);
    try {
      const response = await workspaceApi.createWorkspace(data);
      
      if ('error' in response) {
        setError(response.error);
        return null;
      }

      const newWorkspace = response as Workspace;
      setWorkspaces(prev => [...prev, newWorkspace]);
      return newWorkspace;
    } catch (err) {
      console.error('Failed to create workspace:', err);
      setError('Failed to create workspace');
      return null;
    }
  }, [workspaceApi]);

  // Update workspace
  const updateWorkspace = useCallback(async (workspaceId: string, data: WorkspaceUpdate): Promise<Workspace | null> => {
    setError(null);
    try {
      const response = await workspaceApi.updateWorkspace(workspaceId, data);
      
      if ('error' in response) {
        setError(response.error);
        return null;
      }

      const updatedWorkspace = response as Workspace;
      setWorkspaces(prev => prev.map(w => w.id === workspaceId ? updatedWorkspace : w));
      return updatedWorkspace;
    } catch (err) {
      console.error('Failed to update workspace:', err);
      setError('Failed to update workspace');
      return null;
    }
  }, [workspaceApi]);

  // Archive workspace
  const archiveWorkspace = useCallback(async (workspaceId: string): Promise<boolean> => {
    setError(null);
    try {
      const response = await workspaceApi.archiveWorkspace(workspaceId);
      
      if ('error' in response) {
        setError(response.error);
        return false;
      }

      // Remove from active workspaces list
      setWorkspaces(prev => prev.filter(w => w.id !== workspaceId));
      
      // If archived workspace was current, switch to another
      if (currentWorkspaceId === workspaceId) {
        const remaining = workspaces.filter(w => w.id !== workspaceId);
        if (remaining.length > 0) {
          const personalWorkspace = remaining.find(w => w.type === 'personal');
          const newCurrent = personalWorkspace || remaining[0];
          setCurrentWorkspace(newCurrent.id);
        } else {
          setCurrentWorkspaceId(null);
          setStoredWorkspaceId(null);
        }
      }
      
      return true;
    } catch (err) {
      console.error('Failed to archive workspace:', err);
      setError('Failed to archive workspace');
      return false;
    }
  }, [workspaceApi, currentWorkspaceId, workspaces, setCurrentWorkspace]);

  // Unarchive workspace
  const unarchiveWorkspace = useCallback(async (workspaceId: string): Promise<boolean> => {
    setError(null);
    try {
      const response = await workspaceApi.unarchiveWorkspace(workspaceId);
      
      if ('error' in response) {
        setError(response.error);
        return false;
      }

      await refreshWorkspaces();
      return true;
    } catch (err) {
      console.error('Failed to unarchive workspace:', err);
      setError('Failed to unarchive workspace');
      return false;
    }
  }, [workspaceApi, refreshWorkspaces]);

  // Leave workspace
  const leaveWorkspace = useCallback(async (workspaceId: string): Promise<boolean> => {
    setError(null);
    try {
      const response = await workspaceApi.leaveWorkspace(workspaceId);
      
      if (response && 'error' in response) {
        setError(response.error);
        return false;
      }

      // Remove from workspaces list
      setWorkspaces(prev => prev.filter(w => w.id !== workspaceId));
      
      // If left workspace was current, switch to another
      if (currentWorkspaceId === workspaceId) {
        const remaining = workspaces.filter(w => w.id !== workspaceId);
        if (remaining.length > 0) {
          const personalWorkspace = remaining.find(w => w.type === 'personal');
          const newCurrent = personalWorkspace || remaining[0];
          setCurrentWorkspace(newCurrent.id);
        }
      }
      
      return true;
    } catch (err) {
      console.error('Failed to leave workspace:', err);
      setError('Failed to leave workspace');
      return false;
    }
  }, [workspaceApi, currentWorkspaceId, workspaces, setCurrentWorkspace]);

  // Load workspaces on auth change
  useEffect(() => {
    if (isAuthenticated) {
      refreshWorkspaces();
    }
    // Note: We don't clear workspace on isAuthenticated=false here
    // because auth loading state initially shows as not authenticated
    // Clearing happens explicitly on logout via AuthContext
  }, [isAuthenticated, refreshWorkspaces]);

  const value: WorkspaceContextType = {
    workspaces,
    currentWorkspace,
    currentWorkspaceId,
    isLoading,
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
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};

