import { UserApiClient } from './UserApiClient';
import { CategoryApiClient } from './CategoryApiClient';
import { ExpenseApiClient } from './ExpenseApiClient';
import { IncomeApiClient } from './IncomeApiClient';
import { AccountApiClient } from './AccountApiClient';
import { 
  LoginRequest, 
  CreateUserRequest, 
  ApiResponse,
  LoginResponse 
} from '../../types/api';

export interface ApiClientConfig {
  userServiceUrl?: string;
  categoryServiceUrl?: string;
  expenseServiceUrl?: string;
  incomeServiceUrl?: string;
  accountServiceUrl?: string;
  currencyServiceUrl?: string;
  debtServiceUrl?: string;
  goalServiceUrl?: string;
  recurringServiceUrl?: string;
}

export class ApiClient {
  public user: UserApiClient;
  public category: CategoryApiClient;
  public expense: ExpenseApiClient;
  public income: IncomeApiClient;
  public account: AccountApiClient;

  private token: string | null = null;

  constructor(config: ApiClientConfig) {
    // Default service URLs (can be overridden via config)
    const defaultUrls = {
      userServiceUrl: 'http://localhost:8001',
      categoryServiceUrl: 'http://localhost:8002',
      expenseServiceUrl: 'http://localhost:8003',
      incomeServiceUrl: 'http://localhost:8004',
      accountServiceUrl: 'http://localhost:8005',
      currencyServiceUrl: 'http://localhost:8006',
      debtServiceUrl: 'http://localhost:8007',
      goalServiceUrl: 'http://localhost:8008',
      recurringServiceUrl: 'http://localhost:8009',
    };

    const urls = { ...defaultUrls, ...config };

    // Initialize API clients
    this.user = new UserApiClient(`${urls.userServiceUrl}/users`);
    this.category = new CategoryApiClient(`${urls.categoryServiceUrl}/categories`);
    this.expense = new ExpenseApiClient(`${urls.expenseServiceUrl}/expenses`);
    this.income = new IncomeApiClient(`${urls.incomeServiceUrl}/incomes`);
    this.account = new AccountApiClient(`${urls.accountServiceUrl}/accounts`);
  }

  public setToken(token: string): void {
    this.token = token;
    // Set token for all API clients
    this.user.setToken(token);
    this.category.setToken(token);
    this.expense.setToken(token);
    this.income.setToken(token);
    this.account.setToken(token);
  }

  public clearToken(): void {
    this.token = null;
    // Clear token for all API clients
    this.user.clearToken();
    this.category.clearToken();
    this.expense.clearToken();
    this.income.clearToken();
    this.account.clearToken();
  }

  public getToken(): string | null {
    return this.token;
  }

  public isAuthenticated(): boolean {
    return this.token !== null;
  }

  // Convenience methods for authentication
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await this.user.loginAndSetToken(credentials);
    if (response.data) {
      this.setToken(response.data.access_token);
    }
    return response;
  }

  async register(userData: CreateUserRequest): Promise<ApiResponse<any>> {
    return this.user.register(userData);
  }

  async logout(): Promise<ApiResponse<void>> {
    const response = await this.user.logout();
    this.clearToken();
    return response;
  }

  // Helper method to check if all services are available
  async healthCheck(): Promise<Record<string, boolean>> {
    const services = {
      user: false,
      category: false,
      expense: false,
      income: false,
      account: false,
    };

    try {
      // Simple health checks - you might need to adjust these based on your actual endpoints
      await this.user.getCurrentUser();
      services.user = true;
    } catch {
      services.user = false;
    }

    try {
      await this.category.getCategories({ size: 1 });
      services.category = true;
    } catch {
      services.category = false;
    }

    try {
      await this.expense.getExpenses();
      services.expense = true;
    } catch {
      services.expense = false;
    }

    try {
      await this.income.getIncomes();
      services.income = true;
    } catch {
      services.income = false;
    }

    try {
      await this.account.getAccounts({ size: 1 });
      services.account = true;
    } catch {
      services.account = false;
    }

    return services;
  }
}
