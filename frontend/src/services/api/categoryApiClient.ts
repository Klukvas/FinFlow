import { Category, CreateCategoryRequest, CreateCategoryResponse, CategoryListResponse, CategoryFilters } from '@types';
import { AuthHttpClient } from './AuthHttpClient';
import { config } from '@/config/env';

export interface ErrorResponse {
  error: string;
}

export interface MccBatchResult {
  mcc_code: number;
  success: boolean;
  category_id: number | null;
  category_name: string | null;
  error: string | null;
}

export interface MccBatchResponse {
  results: MccBatchResult[];
  total_requested: number;
  successful: number;
  failed: number;
  language: string;
}

export class CategoryApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.categoryServiceUrl}/categories`,
      getToken,
      refreshToken
    );
  }

  async createCategory(data: CreateCategoryRequest): Promise<CreateCategoryResponse | ErrorResponse> {
    return this.httpClient.post<CreateCategoryResponse>('/', data);
  }

  async getCategories(flat: boolean = false): Promise<Category[] | ErrorResponse> {
    const params = flat ? '?flat=true' : '';
    const response = await this.httpClient.get<CategoryListResponse>(`/${params}`);
    
    // If it's an error, return it as is
    if ('error' in response) {
      return response;
    }
    
    // Extract the items array from the CategoryListResponse
    return response.items || [];
  }

  async getCategoriesPaginated(filters: CategoryFilters = {}): Promise<CategoryListResponse | ErrorResponse> {
    const params = new URLSearchParams();
    
    if (filters.flat !== undefined) {
      params.append('flat', filters.flat.toString());
    }
    if (filters.page !== undefined) {
      params.append('page', filters.page.toString());
    }
    if (filters.size !== undefined) {
      params.append('size', filters.size.toString());
    }
    
    const queryString = params.toString();
    const url = queryString ? `/?${queryString}` : '/';
    
    return this.httpClient.get<CategoryListResponse>(url);
  }

  async getCategory(id: number): Promise<Category | ErrorResponse> {
    return this.httpClient.get<Category>(`/${id}`);
  }

  async getCategoryChildren(id: number): Promise<Category[] | ErrorResponse> {
    return this.httpClient.get<Category[]>(`/${id}/children`);
  }

  async updateCategory(id: number, data: CreateCategoryRequest): Promise<Category | ErrorResponse> {
    return this.httpClient.put<Category>(`/${id}`, data);
  }

  async deleteCategory(id: number): Promise<void | ErrorResponse> {
    return this.httpClient.delete<void>(`/${id}`);
  }

  async createCategoryFromMcc(mccCode: number, language: string = 'ru'): Promise<Category | ErrorResponse> {
    return this.httpClient.post<Category>(`/from-mcc?language=${language}`, { mcc_code: mccCode });
  }

  async createCategoriesFromMccBatch(
    categories: Array<{
      mcc_code: number;
      custom_name?: string;
      parent_id?: number;
      type?: 'EXPENSE' | 'INCOME';
    }>,
    language: string = 'ru'
  ): Promise<MccBatchResponse | ErrorResponse> {
    return this.httpClient.post<MccBatchResponse>(`/from-mcc/batch`, {
      categories,
      language
    });
  }
}