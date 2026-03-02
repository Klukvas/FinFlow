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
  MyInviteListResponse,
  InviteStatus,
  ErrorResponse,
} from "@/types";
import { AuthHttpClient } from "./AuthHttpClient";
import { config } from "@/config/env";

export class WorkspaceApiClient {
  private httpClient: AuthHttpClient;
  private meInvitesClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    // Skip X-Workspace-Id header for workspace service - it manages workspaces itself
    this.httpClient = new AuthHttpClient(
      config.api.workspaceServiceUrl,
      getToken,
      refreshToken,
      true, // skipWorkspaceHeader
    );

    // Separate client for /me/invites endpoints (different base path)
    const meInvitesUrl = import.meta.env.PROD
      ? "/api/me/invites"
      : "http://localhost:8012/me/invites";
    this.meInvitesClient = new AuthHttpClient(
      meInvitesUrl,
      getToken,
      refreshToken,
      true, // skipWorkspaceHeader
    );
  }

  // ==================== Workspaces ====================
  // Note: baseUrl is /api/workspaces, so endpoints don't include /workspaces prefix

  async getWorkspaces(
    includeArchived: boolean = false,
  ): Promise<WorkspaceListResponse | ErrorResponse> {
    const params = includeArchived ? "?include_archived=true" : "";
    return this.httpClient.get<WorkspaceListResponse>(params);
  }

  async getWorkspace(workspaceId: string): Promise<Workspace | ErrorResponse> {
    return this.httpClient.get<Workspace>(`/${workspaceId}`);
  }

  async createWorkspace(
    data: WorkspaceCreate,
  ): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>("", data);
  }

  async updateWorkspace(
    workspaceId: string,
    data: WorkspaceUpdate,
  ): Promise<Workspace | ErrorResponse> {
    return this.httpClient.patch<Workspace>(`/${workspaceId}`, data);
  }

  async archiveWorkspace(
    workspaceId: string,
  ): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(`/${workspaceId}:archive`);
  }

  async unarchiveWorkspace(
    workspaceId: string,
  ): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(`/${workspaceId}:unarchive`);
  }

  async leaveWorkspace(workspaceId: string): Promise<void | ErrorResponse> {
    return this.httpClient.post<void>(`/${workspaceId}:leave`);
  }

  async transferOwnership(
    workspaceId: string,
    newOwnerId: number,
  ): Promise<Workspace | ErrorResponse> {
    return this.httpClient.post<Workspace>(
      `/${workspaceId}/owner:transfer?new_owner_id=${newOwnerId}`,
    );
  }

  // ==================== Members ====================

  async getMembers(
    workspaceId: string,
  ): Promise<WorkspaceMemberListResponse | ErrorResponse> {
    return this.httpClient.get<WorkspaceMemberListResponse>(
      `/${workspaceId}/members`,
    );
  }

  async updateMemberRole(
    workspaceId: string,
    userId: number,
    data: WorkspaceMemberUpdate,
  ): Promise<WorkspaceMember | ErrorResponse> {
    return this.httpClient.patch<WorkspaceMember>(
      `/${workspaceId}/members/${userId}`,
      data,
    );
  }

  async removeMember(
    workspaceId: string,
    userId: number,
  ): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/${workspaceId}/members/${userId}`);
  }

  // ==================== Workspace Invites (Owner Operations) ====================

  /**
   * Get pending invites for a workspace (owner only)
   */
  async getWorkspaceInvites(
    workspaceId: string,
    status?: InviteStatus,
  ): Promise<WorkspaceInviteListResponse | ErrorResponse> {
    const params = status ? `?status=${status}` : "";
    return this.httpClient.get<WorkspaceInviteListResponse>(
      `/${workspaceId}/invites${params}`,
    );
  }

  /**
   * Create an invite by email (owner only)
   */
  async createInvite(
    workspaceId: string,
    data: WorkspaceInviteCreate,
  ): Promise<WorkspaceInvite | ErrorResponse> {
    return this.httpClient.post<WorkspaceInvite>(
      `/${workspaceId}/invites`,
      data,
    );
  }

  /**
   * Cancel a pending invite (owner only)
   */
  async cancelInvite(
    workspaceId: string,
    inviteId: string,
  ): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/${workspaceId}/invites/${inviteId}`);
  }

  // ==================== My Invites (Invitee Operations) ====================
  // Note: These use meInvitesClient with baseUrl /api/me/invites

  /**
   * Get all incoming invites for current user
   * @param includeAll - If true, includes non-pending invites (accepted, rejected, expired)
   */
  async getMyInvites(
    includeAll: boolean = false,
  ): Promise<MyInviteListResponse | ErrorResponse> {
    const params = includeAll ? "?include_all=true" : "";
    return this.meInvitesClient.get<MyInviteListResponse>(params);
  }

  /**
   * Accept an invite
   */
  async acceptInvite(
    inviteId: string,
  ): Promise<WorkspaceInvite | ErrorResponse> {
    return this.meInvitesClient.post<WorkspaceInvite>(`/${inviteId}:accept`);
  }

  /**
   * Reject an invite
   */
  async rejectInvite(inviteId: string): Promise<void | ErrorResponse> {
    return this.meInvitesClient.post<void>(`/${inviteId}:reject`);
  }
}
