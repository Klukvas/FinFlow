export type WorkspaceType = 'personal' | 'shared';

// Simplified roles: owner (manage), full (edit), read (view only)
export type WorkspaceRole = 'owner' | 'full' | 'read';

// Role that can be assigned to invites/members (not owner)
export type AssignableRole = 'full' | 'read';

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
  status: 'active' | 'left' | 'removed';
  joined_at: string;
  created_at: string;
  updated_at: string | null;
  // User details (fetched from user service)
  email?: string | null;
  username?: string | null;
}

export interface WorkspaceMemberUpdate {
  role: AssignableRole;
}

export interface WorkspaceMemberListResponse {
  members: WorkspaceMember[];
  total: number;
}

// Invite statuses
export type InviteStatus = 'pending' | 'accepted' | 'rejected' | 'expired' | 'canceled';

// Invite as seen by workspace owner
export interface WorkspaceInvite {
  id: string;
  workspace_id: string;
  inviter_user_id: number;
  invitee_user_id: number;
  invitee_email: string;
  role: AssignableRole;
  status: InviteStatus;
  expires_at: string;
  created_at: string;
  responded_at: string | null;
  is_expired: boolean;
}

// Rich invite response for invitee (includes workspace/inviter info)
export interface MyInvite {
  id: string;
  workspace_id: string;
  workspace_name: string;
  inviter_user_id: number;
  inviter_email: string;
  inviter_username: string;
  role: AssignableRole;
  status: InviteStatus;
  expires_at: string;
  created_at: string;
  is_expired: boolean;
  is_actionable: boolean;
}

export interface MyInviteListResponse {
  invites: MyInvite[];
  total: number;
}

export interface WorkspaceInviteListResponse {
  invites: WorkspaceInvite[];
  total: number;
}

export interface WorkspaceInviteCreate {
  email: string;
  role?: AssignableRole;
}
