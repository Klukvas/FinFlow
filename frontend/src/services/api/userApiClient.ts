import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: number;
  email: string;
  username: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export type ApiResponse<T> = T | ApiError;

export class UserApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.baseUrl}/auth`,
      getToken,
      refreshToken
    );
  }

  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return this.httpClient.post<LoginResponse>('/login', data);
  }

  async register(data: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    return this.httpClient.post<LoginResponse>('/register', data);
  }

  async getProfile(): Promise<ApiResponse<UserProfile>> {
    return this.httpClient.get<UserProfile>('/me');
  }

  async updateProfile(userData: UserUpdate): Promise<ApiResponse<UserProfile>> {
    return this.httpClient.put<UserProfile>('/me', userData);
  }

  async changePassword(passwordData: PasswordChange): Promise<ApiResponse<{ detail: string }>> {
    return this.httpClient.post<{ detail: string }>('/change-password', passwordData);
  }
}