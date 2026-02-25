import { config } from "@/config/env";
import { HttpClient } from "./httpClient";
import {
  User,
  AdminUser,
  AdminUsersResponse,
  LoginResponse,
  RefreshResponse,
  ApiError,
} from "@/types";

export class UserService {
  private client: HttpClient;

  constructor(
    getToken: () => string | null,
    onUnauthorized?: () => void,
    onRefreshToken?: () => Promise<string | null>,
  ) {
    this.client = new HttpClient(
      config.api.userServiceUrl,
      getToken,
      onUnauthorized,
      onRefreshToken,
    );
  }

  // Auth endpoints
  async login(
    email: string,
    password: string,
  ): Promise<LoginResponse | ApiError> {
    return this.client.post<LoginResponse>("/auth/login", { email, password });
  }

  async refreshToken(
    refreshToken: string,
  ): Promise<RefreshResponse | ApiError> {
    return this.client.post<RefreshResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
  }

  async getMe(): Promise<User | ApiError> {
    return this.client.get<User>("/auth/me");
  }

  // Admin endpoints
  async listUsers(params: {
    search?: string;
    page?: number;
    pageSize?: number;
  }): Promise<AdminUsersResponse | ApiError> {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.page) query.set("page", params.page.toString());
    if (params.pageSize) query.set("page_size", params.pageSize.toString());

    const queryString = query.toString();
    return this.client.get<AdminUsersResponse>(
      `/admin/users${queryString ? `?${queryString}` : ""}`,
    );
  }

  async getUser(userId: number): Promise<AdminUser | ApiError> {
    return this.client.get<AdminUser>(`/admin/users/${userId}`);
  }

  async updateUserRole(
    userId: number,
    role: string,
  ): Promise<AdminUser | ApiError> {
    return this.client.patch<AdminUser>(`/admin/users/${userId}/role`, {
      role,
    });
  }

  async updateUserStatus(
    userId: number,
    status: string,
  ): Promise<AdminUser | ApiError> {
    return this.client.patch<AdminUser>(`/admin/users/${userId}/status`, {
      status,
    });
  }

  async getHealth(): Promise<{ status: string } | ApiError> {
    return this.client.get("/health");
  }
}
