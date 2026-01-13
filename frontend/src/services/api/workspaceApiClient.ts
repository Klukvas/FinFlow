import { 
  Workspace, 
  WorkspaceCreate, 
  WorkspaceUpdate, 
  WorkspaceListResponse,
  WorkspaceMember,
  WorkspaceMemberListResponse,
  WorkspaceMemberUpdate,
  WorkspaceInvite,
  WorkspaceInviteCreate,
  WorkspaceInviteListResponse,
  MyInvite,
  MyInviteListResponse,
  InviteStatus,
  ErrorResponse 
} from '@/types';
import { AuthHttpClient } from './AuthHttpClient';
import { config } from '@/config/env';

export class WorkspaceApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    // Skip X-Workspace-Id header for workspace service - it manages workspaces itself
    this.httpClient = new AuthHttpClient(
      config.api.workspaceServiceUrl,
      getToken,
      refreshToken,
      true // skipWorkspaceHeader
    );
  }

  // ==================== Workspaces ====================

  async getWorkspaces(includeArchived: boolean = false): Promise<WorkspaceListResponse | ErrorResponse> {
    const params = includeArchived ? '?include_archived=true' : '';
    return this.httpClient.get<WorkspaceListResponse>(`/workspaces${params}`);
  }

  async getWorkspace(workspaceId: string): Promise<Workspace | ErrorResponse> {
    return this.httpClient.get<Workspace>(`/workspaces/${workspaceId}`);
  }

  async createWorkspace(data: WorkspaceCreate): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>('/workspaces', data);
  }

  async updateWorkspace(workspaceId: string, data: WorkspaceUpdate): Promise<Workspace | ErrorResponse> {
    return this.httpClient.patch<Workspace>(`/workspaces/${workspaceId}`, data);
  }

  async archiveWorkspace(workspaceId: string): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(`/workspaces/${workspaceId}:archive`);
  }

  async unarchiveWorkspace(workspaceId: string): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(`/workspaces/${workspaceId}:unarchive`);
  }

  async leaveWorkspace(workspaceId: string): Promise<void | ErrorResponse> {
    return this.httpClient.post<void>(`/workspaces/${workspaceId}:leave`);
  }

  async transferOwnership(workspaceId: string, newOwnerId: number): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(`/workspaces/${workspaceId}/owner:transfer?new_owner_id=${newOwnerId}`);
  }

  // ==================== Members ====================

  async getMembers(workspaceId: string): Promise<WorkspaceMemberListResponse | ErrorResponse> {
    return this.httpClient.get<WorkspaceMemberListResponse>(`/workspaces/${workspaceId}/members`);
  }

  async updateMemberRole(workspaceId: string, userId: number, data: WorkspaceMemberUpdate): Promise<WorkspaceMember | ErrorResponse> {
    return this.httpClient.patch<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, data);
  }

  async removeMember(workspaceId: string, userId: number): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/workspaces/${workspaceId}/members/${userId}`);
  }

  // ==================== Workspace Invites (Owner Operations) ====================

  /**
   * Get pending invites for a workspace (owner only)
   */
  async getWorkspaceInvites(workspaceId: string, status?: InviteStatus): Promise<WorkspaceInviteListResponse | ErrorResponse> {
    const params = status ? `?status=${status}` : '';
    return this.httpClient.get<WorkspaceInviteListResponse>(`/workspaces/${workspaceId}/invites${params}`);
  }

  /**
   * Create an invite by email (owner only)
   */
  async createInvite(workspaceId: string, data: WorkspaceInviteCreate): Promise<WorkspaceInvite | ErrorResponse> {
    return this.httpClient.post<WorkspaceInvite>(`/workspaces/${workspaceId}/invites`, data);
  }

  /**
   * Cancel a pending invite (owner only)
   */
  async cancelInvite(workspaceId: string, inviteId: string): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/workspaces/${workspaceId}/invites/${inviteId}`);
  }

  // ==================== My Invites (Invitee Operations) ====================

  /**
   * Get all incoming invites for current user
   * @param includeAll - If true, includes non-pending invites (accepted, rejected, expired)
   */
  async getMyInvites(includeAll: boolean = false): Promise<MyInviteListResponse | ErrorResponse> {
    const params = includeAll ? '?include_all=true' : '';
    return this.httpClient.get<MyInviteListResponse>(`/me/invites${params}`);
  }

  /**
   * Accept an invite
   */
  async acceptInvite(inviteId: string): Promise<WorkspaceInvite | ErrorResponse> {
    return this.httpClient.post<WorkspaceInvite>(`/me/invites/${inviteId}:accept`);
  }

  /**
   * Reject an invite
   */
  async rejectInvite(inviteId: string): Promise<void | ErrorResponse> {
    return this.httpClient.post<void>(`/me/invites/${inviteId}:reject`);
  }
}
