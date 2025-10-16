import { BaseApiClient } from './BaseApiClient';
import { 
  Expense, 
  CreateExpenseRequest, 
  UpdateExpenseRequest,
  PaginatedResponse,
  ApiResponse 
} from '../../types/api';

export interface ExpenseFilters {
  page?: number;
  size?: number;
}

export class ExpenseApiClient extends BaseApiClient {
  constructor(baseURL: string) {
    super({ baseURL });
  }

  async getExpenses(): Promise<ApiResponse<Expense[]>> {
    return this.makeRequest(async () => {
      return await this.get<Expense[]>('/');
    });
  }

  async getExpensesPaginated(filters: ExpenseFilters = {}): Promise<ApiResponse<PaginatedResponse<Expense>>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/paginated?${queryString}` : '/paginated';
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Expense>>(url);
    });
  }

  async getExpense(id: number): Promise<ApiResponse<Expense>> {
    return this.makeRequest(async () => {
      return await this.get<Expense>(`/${id}`);
    });
  }

  async createExpense(data: CreateExpenseRequest): Promise<ApiResponse<Expense>> {
    return this.makeRequest(async () => {
      return await this.post<Expense>('/', data);
    });
  }

  async updateExpense(id: number, data: UpdateExpenseRequest): Promise<ApiResponse<Expense>> {
    return this.makeRequest(async () => {
      return await this.patch<Expense>(`/${id}`, data);
    });
  }

  async deleteExpense(id: number): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>(`/${id}`);
    });
  }

  async getExpensesByCategory(categoryId: number): Promise<ApiResponse<Expense[]>> {
    return this.makeRequest(async () => {
      return await this.get<Expense[]>(`/category/${categoryId}`);
    });
  }

  async getExpensesByCategoryPaginated(categoryId: number, filters: ExpenseFilters = {}): Promise<ApiResponse<PaginatedResponse<Expense>>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/category/${categoryId}/paginated?${queryString}` : `/category/${categoryId}/paginated`;
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Expense>>(url);
    });
  }

  async getExpensesByDateRange(startDate: string, endDate: string): Promise<ApiResponse<Expense[]>> {
    return this.makeRequest(async () => {
      return await this.get<Expense[]>(`/date-range/?start_date=${startDate}&end_date=${endDate}`);
    });
  }

  async getExpensesByDateRangePaginated(startDate: string, endDate: string, filters: ExpenseFilters = {}): Promise<ApiResponse<PaginatedResponse<Expense>>> {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = `/date-range/paginated?${queryString}`;
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Expense>>(url);
    });
  }
}
