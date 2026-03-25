import { AccountApiClient } from "../../infra/api/AccountApiClient";
import { CreateAccountRequest } from "../../types/api";

export class AccountApiActions {
  private accountApiClient: AccountApiClient;

  constructor(accountApiClient: AccountApiClient) {
    this.accountApiClient = accountApiClient;
  }

  async createAccount(
    token: string,
    data: CreateAccountRequest,
    workspaceId?: string,
  ): Promise<{ id: number; name: string; balance: number; currency: string }> {
    this.accountApiClient.setToken(token);
    if (workspaceId) {
      this.accountApiClient.setWorkspaceId(workspaceId);
    }

    const response = await this.accountApiClient.createAccount(data);

    if (response.error || !response.data) {
      throw new Error(`Failed to create account: ${response.error}`);
    }

    return response.data;
  }

  async deleteAllAccounts(
    token: string,
    workspaceId?: string,
  ): Promise<number> {
    this.accountApiClient.setToken(token);
    if (workspaceId) {
      this.accountApiClient.setWorkspaceId(workspaceId);
    }

    const response = await this.accountApiClient.getAllAccounts();

    if (response.error) {
      throw new Error(`Failed to fetch accounts: ${response.error}`);
    }
    if (!response.data) {
      return 0;
    }

    const accounts = response.data;
    let deletedCount = 0;

    for (const account of accounts) {
      try {
        await this.accountApiClient.deleteAccount(account.id);
        deletedCount++;
      } catch (error: any) {
        console.error(
          `Failed to delete account ${account.id}: ${error.message}`,
        );
      }
    }

    return deletedCount;
  }

  async getAccountBalance(
    token: string,
    accountId: number,
    workspaceId?: string,
  ): Promise<{ balance: number; currency: string }> {
    this.accountApiClient.setToken(token);
    if (workspaceId) {
      this.accountApiClient.setWorkspaceId(workspaceId);
    }

    const response = await this.accountApiClient.getAccount(accountId);

    if (response.error || !response.data) {
      throw new Error(`Failed to get account: ${response.error}`);
    }

    return {
      balance: response.data.balance,
      currency: response.data.currency,
    };
  }
}
