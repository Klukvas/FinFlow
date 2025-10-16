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
}