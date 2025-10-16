import { BaseApiClient } from './BaseApiClient';
import { 
  Account, 
  CreateAccountRequest, 
  UpdateAccountRequest,
  PaginatedResponse,
  ApiResponse 
} from '../../types/api';

export interface AccountFilters {
  page?: number;
  size?: number;
}

export class AccountApiClient extends BaseApiClient {
  constructor(baseURL: string) {
    super({ baseURL });
  }

  async getAccounts(filters: AccountFilters = {}): Promise<ApiResponse<PaginatedResponse<Account>>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/?${queryString}` : '/';
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Account>>(url);
    });
  }

  async getAccount(id: number): Promise<ApiResponse<Account>> {
    return this.makeRequest(async () => {
      return await this.get<Account>(`/${id}`);
    });
  }

  async createAccount(data: CreateAccountRequest): Promise<ApiResponse<Account>> {
    return this.makeRequest(async () => {
      return await this.post<Account>('/', data);
    });
  }

  async updateAccount(id: number, data: UpdateAccountRequest): Promise<ApiResponse<Account>> {
    return this.makeRequest(async () => {
      return await this.patch<Account>(`/${id}`, data);
    });
  }

  async deleteAccount(id: number): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>(`/${id}`);
    });
  }

  async getAccountBalance(id: number): Promise<ApiResponse<{ balance: number; currency: string }>> {
    return this.makeRequest(async () => {
      return await this.get<{ balance: number; currency: string }>(`/${id}/balance`);
    });
  }

  async updateAccountBalance(id: number, amount: number, currency: string): Promise<ApiResponse<Account>> {
    return this.makeRequest(async () => {
      return await this.post<Account>(`/${id}/balance`, { amount, currency });
    });
  }

  // Helper methods
  async getAllAccounts(): Promise<ApiResponse<Account[]>> {
    const response = await this.getAccounts({ size: 1000 });
    if (response.data) {
      return { data: response.data.items };
    }
    return response;
  }
}
