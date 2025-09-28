import { Category, CreateCategoryRequest, CreateCategoryResponse } from '@types';
import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export interface ErrorResponse {
  error: string;
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
    return this.httpClient.get<Category[]>(`/${params}`);
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
}