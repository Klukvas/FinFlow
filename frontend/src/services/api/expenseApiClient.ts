import { CreateExpenseRequest, ErrorResponse, ExpenseResponse, ExpenseUpdate } from '@/types';
import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export class ExpenseApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.expenseServiceUrl}/expenses`,
      getToken,
      refreshToken
    );
  }

  async createExpense(data: CreateExpenseRequest): Promise<ExpenseResponse | { error: string }> {
    return this.httpClient.post<ExpenseResponse>('/', data);
  }

  async getExpenses(): Promise<ExpenseResponse[] | { error: string }> {
    return this.httpClient.get<ExpenseResponse[]>('/');
  }

  async getExpense(id: number): Promise<ExpenseResponse | ErrorResponse> {
    return this.httpClient.get<ExpenseResponse>(`/${id}`);
  }

  async updateExpense(id: number, data: ExpenseUpdate): Promise<ExpenseResponse | ErrorResponse> {
    return this.httpClient.patch<ExpenseResponse>(`/${id}`, data);
  }

  async deleteExpense(id: number): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/${id}`);
  }
}