export type WorkspaceType = 'personal' | 'shared';

export type WorkspaceRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface Workspace {
  id: string;
  name: string;
  type: WorkspaceType;
  owner_user_id: number;
  created_at: string;
  updated_at: string | null;
  archived_at: string | null;
  is_archived: boolean;
  member_count: number | null;
  current_user_role: WorkspaceRole | null;
}

export interface WorkspaceCreate {
  name: string;
  type?: WorkspaceType;
}

export interface WorkspaceUpdate {
  name?: string;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
  total: number;
}

export interface WorkspaceMember {
  id: number;
  workspace_id: string;
  user_id: number;
  role: WorkspaceRole;
  joined_at: string;
  invited_by: number | null;
  username?: string;
  email?: string;
}

export interface WorkspaceMemberCreate {
  user_id: number;
  role: WorkspaceRole;
}

export interface WorkspaceMemberUpdate {
  role: WorkspaceRole;
}

export interface WorkspaceMemberListResponse {
  members: WorkspaceMember[];
  total: number;
}

export interface WorkspaceInvite {
  id: number;
  workspace_id: string;
  email: string;
  role: WorkspaceRole;
  token: string;
  expires_at: string;
  used_at: string | null;
  created_by: number;
  created_at: string;
}

export interface WorkspaceInviteCreate {
  email: string;
  role?: WorkspaceRole;
}

