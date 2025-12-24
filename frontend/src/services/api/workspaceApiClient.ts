import { 
  Workspace, 
  WorkspaceCreate, 
  WorkspaceUpdate, 
  WorkspaceListResponse,
  WorkspaceMember,
  WorkspaceMemberListResponse,
  WorkspaceInvite,
  WorkspaceInviteCreate,
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

  async addMember(workspaceId: string, userId: number, role: string = 'member'): Promise<WorkspaceMember | ErrorResponse> {
    return this.httpClient.post<WorkspaceMember>(`/workspaces/${workspaceId}/members`, { user_id: userId, role });
  }

  async updateMemberRole(workspaceId: string, userId: number, role: string): Promise<WorkspaceMember | ErrorResponse> {
    return this.httpClient.patch<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, { role });
  }

  async removeMember(workspaceId: string, userId: number): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/workspaces/${workspaceId}/members/${userId}`);
  }

  // ==================== Invites ====================

  async getInvites(workspaceId: string): Promise<WorkspaceInvite[] | ErrorResponse> {
    return this.httpClient.get<WorkspaceInvite[]>(`/workspaces/${workspaceId}/invites`);
  }

  async createInvite(workspaceId: string, data: WorkspaceInviteCreate): Promise<WorkspaceInvite | ErrorResponse> {
    return this.httpClient.post<WorkspaceInvite>(`/workspaces/${workspaceId}/invites`, data);
  }

  async acceptInvite(token: string): Promise<WorkspaceMember | ErrorResponse> {
    return this.httpClient.post<WorkspaceMember>(`/invites/${token}/accept`);
  }

  async declineInvite(token: string): Promise<void | ErrorResponse> {
    return this.httpClient.post<void>(`/invites/${token}/decline`);
  }

  async revokeInvite(workspaceId: string, inviteId: number): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/workspaces/${workspaceId}/invites/${inviteId}`);
  }
}

