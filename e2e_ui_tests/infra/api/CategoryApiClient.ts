import { BaseApiClient } from './BaseApiClient';
import { 
  Category, 
  CreateCategoryRequest, 
  UpdateCategoryRequest,
  PaginatedResponse,
  ApiResponse,
} from '../../types/api';

export interface CategoryFilters {
  flat?: boolean;
  page?: number;
  size?: number;
}

export class CategoryApiClient extends BaseApiClient {
  constructor(baseURL: string) {
    super({ baseURL });
  }

  async getCategories(filters: CategoryFilters = {}): Promise<ApiResponse<PaginatedResponse<Category>>> {
    const params = new URLSearchParams();
    if (filters.flat !== undefined) params.append('flat', filters.flat.toString());
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.size) params.append('size', filters.size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/categories/?${queryString}` : '/categories/';
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Category>>(url);
    });
  }

  async getCategory(id: number): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.get<Category>(`/categories/${id}`);
    });
  }

  async createCategory(data: CreateCategoryRequest): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.post<Category>('/categories/', data);
    });
  }

  async updateCategory(id: number, data: UpdateCategoryRequest): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.put<Category>(`/categories/${id}`, data);
    });
  }

  async deleteCategory(id: number): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>(`/categories/${id}`);
    });
  }

  async getCategoryChildren(id: number): Promise<ApiResponse<Category[]>> {
    return this.makeRequest(async () => {
      return await this.get<Category[]>(`/${id}/children`);
    });
  }

  // Helper methods for common operations
  async getAllCategoriesFlat(): Promise<ApiResponse<Category[]>> {
    const response = await this.getCategories({ flat: true, size: 100 });
    
    if (response.data) {
      return { data: response.data.items };
    }
    
    return { error: response.error || 'No categories found' };
  }

  async getRootCategories(): Promise<ApiResponse<Category[]>> {
    const response = await this.getCategories({ flat: false, size: 1000 });
    if (response.data) {
      return { data: response.data.items };
    }
    return { error: response.error || 'No categories found' };
  }

}
