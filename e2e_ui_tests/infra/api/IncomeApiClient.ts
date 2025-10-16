import { BaseApiClient } from './BaseApiClient';
import { 
  Income, 
  CreateIncomeRequest, 
  UpdateIncomeRequest,
  PaginatedResponse,
  ApiResponse 
} from '../../types/api';

export interface IncomeFilters {
  page?: number;
  size?: number;
}

export class IncomeApiClient extends BaseApiClient {
  constructor(baseURL: string) {
    super({ baseURL });
  }

  async getIncomes(): Promise<ApiResponse<Income[]>> {
    return this.makeRequest(async () => {
      return await this.get<Income[]>('/');
    });
  }

  async getIncomesPaginated(filters: IncomeFilters = {}): Promise<ApiResponse<PaginatedResponse<Income>>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/paginated?${queryString}` : '/paginated';
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Income>>(url);
    });
  }

  async getIncome(id: number): Promise<ApiResponse<Income>> {
    return this.makeRequest(async () => {
      return await this.get<Income>(`/${id}`);
    });
  }

  async createIncome(data: CreateIncomeRequest): Promise<ApiResponse<Income>> {
    return this.makeRequest(async () => {
      return await this.post<Income>('/', data);
    });
  }

  async updateIncome(id: number, data: UpdateIncomeRequest): Promise<ApiResponse<Income>> {
    return this.makeRequest(async () => {
      return await this.patch<Income>(`/${id}`, data);
    });
  }

  async deleteIncome(id: number): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>(`/${id}`);
    });
  }

  async getIncomesByCategory(categoryId: number): Promise<ApiResponse<Income[]>> {
    return this.makeRequest(async () => {
      return await this.get<Income[]>(`/category/${categoryId}`);
    });
  }

  async getIncomesByCategoryPaginated(categoryId: number, filters: IncomeFilters = {}): Promise<ApiResponse<PaginatedResponse<Income>>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/category/${categoryId}/paginated?${queryString}` : `/category/${categoryId}/paginated`;
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Income>>(url);
    });
  }

  async getIncomesByDateRange(startDate: string, endDate: string): Promise<ApiResponse<Income[]>> {
    return this.makeRequest(async () => {
      return await this.get<Income[]>(`/date-range/?start_date=${startDate}&end_date=${endDate}`);
    });
  }

  async getIncomesByDateRangePaginated(startDate: string, endDate: string, filters: IncomeFilters = {}): Promise<ApiResponse<PaginatedResponse<Income>>> {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = `/date-range/paginated?${queryString}`;
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Income>>(url);
    });
  }
}
