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
    const url = queryString ? `/?${queryString}` : '/';
    
    return this.makeRequest(async () => {
      return await this.get<PaginatedResponse<Category>>(url);
    });
  }

  async getCategory(id: number): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.get<Category>(`/${id}`);
    });
  }

  async createCategory(data: CreateCategoryRequest): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.post<Category>('/', data);
    });
  }

  async updateCategory(id: number, data: UpdateCategoryRequest): Promise<ApiResponse<Category>> {
    return this.makeRequest(async () => {
      return await this.put<Category>(`/${id}`, data);
    });
  }

  async deleteCategory(id: number): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>(`/${id}`);
    });
  }

  async getCategoryChildren(id: number): Promise<ApiResponse<Category[]>> {
    return this.makeRequest(async () => {
      return await this.get<Category[]>(`/${id}/children`);
    });
  }

  // Helper methods for common operations
  async getAllCategoriesFlat(): Promise<ApiResponse<Category[]>> {
    console.log('📡 CategoryApiClient: Calling getCategories with flat=true, size=1000');
    const response = await this.getCategories({ flat: true, size: 1000 });
    console.log('📡 CategoryApiClient: getCategories response:', response);
    
    if (response.data) {
      console.log(`📡 CategoryApiClient: Returning ${response.data.items.length} categories`);
      return { data: response.data.items };
    }
    
    console.log('📡 CategoryApiClient: No data in response, returning error response');
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
