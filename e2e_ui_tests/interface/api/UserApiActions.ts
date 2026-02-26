import { UserApiClient } from "../../infra/api/UserApiClient";

export class UserApiActions {
  private userApiClient: UserApiClient;

  constructor(userApiClient: UserApiClient) {
    this.userApiClient = userApiClient;
  }

  async getToken(email: string, password: string): Promise<string> {
    const response = await this.userApiClient.login({ email, password });
    if (response.error || !response.data?.access_token) {
      throw new Error(`Failed to get token: ${response.error}`);
    }
    return response.data.access_token;
  }

  /**
   * Extract default_workspace_id from JWT token payload
   */
  getWorkspaceIdFromToken(token: string): string {
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
    if (!payload.default_workspace_id) {
      throw new Error('No default_workspace_id in token');
    }
    return payload.default_workspace_id;
  }

  async register({ email, username, password }: { email: string, username?: string, password: string }): Promise<void> {
    const response = await this.userApiClient.register({ email, username, password });
    if (response.error && response.errorCode !== 'EMAIL_ALREADY_TAKEN') {
      throw new Error(`Failed to register: ${response.error}`);
    }
  }

  async registerMultipleUsers(users: { email: string, username?: string, password: string }[]): Promise<void> {
    for (const user of users) {
      await this.register(user);
    }
  }
}
