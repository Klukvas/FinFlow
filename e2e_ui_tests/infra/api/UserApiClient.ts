import { BaseApiClient } from './BaseApiClient';
import { 
  User, 
  CreateUserRequest, 
  LoginRequest, 
  LoginResponse, 
  ApiResponse 
} from '../../types/api';

export class UserApiClient extends BaseApiClient {
  constructor(baseURL: string) {
    super({ baseURL });
  }

  async register(data: CreateUserRequest): Promise<ApiResponse<User>> {
    return this.makeRequest(async () => {
      return await this.post<User>('/users/register', data);
    });
  }

  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return this.makeRequest(async () => {
      return await this.post<LoginResponse>('/auth/login', data);
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.makeRequest(async () => {
      return await this.get<User>('/users/me');
    });
  }

  async updateUser(data: Partial<User>): Promise<ApiResponse<User>> {
    return this.makeRequest(async () => {
      return await this.patch<User>('/users/me', data);
    });
  }

  async deleteUser(): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.delete<void>('/users/me');
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.makeRequest(async () => {
      return await this.post<void>('/users/logout');
    });
  }

  async refreshToken(): Promise<ApiResponse<LoginResponse>> {
    return this.makeRequest(async () => {
      return await this.post<LoginResponse>('/users/refresh');
    });
  }

  // Helper method to login and set token
  async loginAndSetToken(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await this.login(data);
    if (response.data) {
      this.setToken(response.data.access_token);
    }
    return response;
  }
}
