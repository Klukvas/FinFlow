import {
  BankConnection,
  SyncStatus,
  SyncRequest,
  LinkedAccount,
  LinkAccountRequest,
  ConnectionCreate,
  SyncPreviewResponse,
  SyncConfirmTransaction,
} from "@/types/bankSync";
import { AuthHttpClient } from "./AuthHttpClient";
import { config } from "@/config/env";

export class BankSyncApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>,
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.bankSyncServiceUrl}/connections`,
      getToken,
      refreshToken,
    );
  }

  async connect(
    payload: ConnectionCreate,
  ): Promise<BankConnection | { error: string }> {
    return this.httpClient.post<BankConnection>("/", payload);
  }

  async getConnections(): Promise<BankConnection[] | { error: string }> {
    return this.httpClient.get<BankConnection[]>("/");
  }

  async disconnect(connectionId: number): Promise<void | { error: string }> {
    return this.httpClient.delete<void>(`/${connectionId}`);
  }

  async linkAccount(
    connectionId: number,
    linkedAccountId: number,
    payload: LinkAccountRequest,
  ): Promise<LinkedAccount | { error: string }> {
    return this.httpClient.put<LinkedAccount>(
      `/${connectionId}/accounts/${linkedAccountId}/link`,
      payload,
    );
  }

  async toggleAccountSync(
    connectionId: number,
    linkedAccountId: number,
  ): Promise<LinkedAccount | { error: string }> {
    return this.httpClient.put<LinkedAccount>(
      `/${connectionId}/accounts/${linkedAccountId}/toggle`,
    );
  }

  async triggerSync(
    connectionId: number,
    request?: SyncRequest,
  ): Promise<SyncStatus | { error: string }> {
    return this.httpClient.post<SyncStatus>(
      `/${connectionId}/sync`,
      request || {},
    );
  }

  async getSyncStatus(
    connectionId: number,
  ): Promise<SyncStatus | null | { error: string }> {
    return this.httpClient.get<SyncStatus | null>(
      `/${connectionId}/sync/status`,
    );
  }

  async getSyncHistory(
    connectionId: number,
    skip: number = 0,
    limit: number = 20,
  ): Promise<SyncStatus[] | { error: string }> {
    return this.httpClient.get<SyncStatus[]>(
      `/${connectionId}/sync/history?skip=${skip}&limit=${limit}`,
    );
  }

  async previewSync(
    connectionId: number,
    request?: SyncRequest,
  ): Promise<SyncPreviewResponse | { error: string }> {
    return this.httpClient.post<SyncPreviewResponse>(
      `/${connectionId}/sync/preview`,
      request || {},
    );
  }

  async confirmSync(
    connectionId: number,
    body: { days_back: number; transactions: SyncConfirmTransaction[] },
  ): Promise<SyncStatus | { error: string }> {
    return this.httpClient.post<SyncStatus>(
      `/${connectionId}/sync/confirm`,
      body,
    );
  }
}
