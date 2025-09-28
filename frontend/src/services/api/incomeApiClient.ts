import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';
import { IncomeCreate, IncomeOut, IncomeUpdate, IncomeSummary, IncomeStats } from '@/types/income';

export type ApiResponse<T> = T | ApiError;

export class IncomeApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.incomeServiceUrl}/incomes`,
      getToken,
      refreshToken
    );
  }

  async getIncomes(skip: number = 0, limit: number = 100): Promise<ApiResponse<IncomeOut[]>> {
    return this.httpClient.get<IncomeOut[]>(`/?skip=${skip}&limit=${limit}`);
  }

  async getIncome(id: number): Promise<ApiResponse<IncomeOut>> {
    return this.httpClient.get<IncomeOut>(`/${id}`);
  }

  async createIncome(income: IncomeCreate): Promise<ApiResponse<IncomeOut>> {
    return this.httpClient.post<IncomeOut>('/', income);
  }

  async updateIncome(id: number, income: IncomeUpdate): Promise<ApiResponse<IncomeOut>> {
    return this.httpClient.put<IncomeOut>(`/${id}`, income);
  }

  async deleteIncome(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.httpClient.delete<{ message: string }>(`/${id}`);
  }

  async getIncomeSummary(startDate: string, endDate: string): Promise<ApiResponse<IncomeSummary>> {
    return this.httpClient.get<IncomeSummary>(`/stats/summary?start_date=${startDate}&end_date=${endDate}`);
  }

  async getIncomeStats(): Promise<ApiResponse<IncomeStats>> {
    return this.httpClient.get<IncomeStats>('/stats/overview');
  }
}
