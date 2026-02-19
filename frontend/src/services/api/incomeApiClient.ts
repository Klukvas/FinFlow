import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';
import { IncomeCreate, IncomeOut, IncomeUpdate, IncomeSummary, IncomeStats, IncomesByCategoryResponse, IncomeListResponse } from '@/types/income';

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

  async getIncomesPaginated(params: { page?: number; size?: number } = {}): Promise<ApiResponse<IncomeListResponse>> {
    const searchParams = new URLSearchParams();
    if (params.page !== undefined) searchParams.append('page', params.page.toString());
    if (params.size !== undefined) searchParams.append('size', params.size.toString());
    return this.httpClient.get<IncomeListResponse>(`/paginated?${searchParams.toString()}`);
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

  async getIncomesByCategory(category_id: number): Promise<ApiResponse<IncomesByCategoryResponse>> {
    return this.httpClient.get<IncomesByCategoryResponse>(`/category/${category_id}`);
  }

  async getCurrentMonthCount(): Promise<ApiResponse<{ count: number; limit: number | null }>> {
    return this.httpClient.get<{ count: number; limit: number | null }>('/current-month-count');
  }
}
