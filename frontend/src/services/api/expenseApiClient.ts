import { CreateExpenseRequest, ErrorResponse, ExpenseResponse, ExpenseUpdate, ExpenseListResponse, ExpenseFilters } from '@/types';
import { AuthHttpClient } from './AuthHttpClient';
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

  async getExpensesPaginated(filters: ExpenseFilters = {}): Promise<ExpenseListResponse | ErrorResponse> {
    const params = new URLSearchParams();
    
    if (filters.page !== undefined) {
      params.append('page', filters.page.toString());
    }
    if (filters.size !== undefined) {
      params.append('size', filters.size.toString());
    }
    
    const queryString = params.toString();
    const url = queryString ? `/paginated?${queryString}` : '/paginated';
    
    return this.httpClient.get<ExpenseListResponse>(url);
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