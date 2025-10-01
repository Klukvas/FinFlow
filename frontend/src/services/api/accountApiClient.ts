import { 
  AccountCreate, 
  AccountUpdate, 
  AccountResponse, 
  AccountSummary, 
  AccountTransactionSummary,
  CreateAccountRequest,
  ErrorResponse 
} from '@/types';
import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export class AccountApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.accountServiceUrl}/accounts`,
      getToken,
      refreshToken
    );
  }

  async createAccount(data: CreateAccountRequest): Promise<AccountResponse | { error: string }> {
    return this.httpClient.post<AccountResponse>('/', data);
  }

  async getAccounts(): Promise<AccountResponse[] | { error: string }> {
    return this.httpClient.get<AccountResponse[]>('/');
  }

  async getAccount(id: number): Promise<AccountResponse | ErrorResponse> {
    return this.httpClient.get<AccountResponse>(`/${id}`);
  }

  async updateAccount(id: number, data: AccountUpdate): Promise<AccountResponse | ErrorResponse> {
    return this.httpClient.put<AccountResponse>(`/${id}`, data);
  }

  async archiveAccount(id: number): Promise<AccountResponse | ErrorResponse> {
    return this.httpClient.patch<AccountResponse>(`/${id}/archive`);
  }

  async getAccountSummaries(): Promise<AccountSummary[] | { error: string }> {
    return this.httpClient.get<AccountSummary[]>('/summaries');
  }

  async getAccountTransactions(id: number): Promise<AccountTransactionSummary | ErrorResponse> {
    return this.httpClient.get<AccountTransactionSummary>(`/${id}/transactions`);
  }
}
