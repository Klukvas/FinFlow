import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';
import { UserFeature, UserEntitlements, PlanResponse, SubscriptionResponse, PlanWithFeatures } from '@/types/subscription';
import { AccountApiClient } from './accountApiClient';
import { CategoryApiClient } from './categoryApiClient';
import { ExpenseApiClient } from './expenseApiClient';
import { IncomeApiClient } from './incomeApiClient';
import { DebtApiClient } from './debtApiClient';
import { GoalsApiClient } from './goalsApi';

export class SubscriptionApiClient {
  private httpClient: AuthHttpClient;
  private accountApi: AccountApiClient;
  private categoryApi: CategoryApiClient;
  private expenseApi: ExpenseApiClient;
  private incomeApi: IncomeApiClient;
  private debtApi: DebtApiClient;
  private goalsApi: GoalsApiClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.subscriptionServiceUrl}`,
      getToken,
      refreshToken
    );
    
    // Initialize other API clients
    this.accountApi = new AccountApiClient(getToken, refreshToken);
    this.categoryApi = new CategoryApiClient(getToken, refreshToken);
    this.expenseApi = new ExpenseApiClient(getToken, refreshToken);
    this.incomeApi = new IncomeApiClient(getToken, refreshToken);
    this.debtApi = new DebtApiClient(getToken, refreshToken);
    this.goalsApi = new GoalsApiClient(getToken, refreshToken);
  }

  async getUserEntitlements(userId: number): Promise<UserEntitlements | ApiError> {
    return this.httpClient.get<UserEntitlements>(`/v1/entitlements/${userId}`);
  }

  async getUserFeatures(userId: number): Promise<UserFeature[] | ApiError> {
    // Use entitlements endpoint instead of internal features endpoint
    const entitlements = await this.getUserEntitlements(userId);
    if ('error' in entitlements) {
      return entitlements;
    }
    
    // Transform the backend response format to match frontend expectations
    const features: UserFeature[] = Object.entries(entitlements.entitlements).map(([feature_code, data]) => ({
      feature_code,
      enabled: Boolean(data.enabled),
      limit_value: data.limit_value
    }));
    
    return features;
  }

  async getPlans(): Promise<PlanResponse[] | ApiError> {
    return this.httpClient.get<PlanResponse[]>('/v1/plans');
  }

  async getPlansWithFeatures(): Promise<PlanWithFeatures[] | ApiError> {
    return this.httpClient.get<PlanWithFeatures[]>('/v1/plans/with-features');
  }

  async getUserSubscription(userId: number): Promise<SubscriptionResponse | ApiError> {
    return this.httpClient.get<SubscriptionResponse>(`/v1/subscriptions/${userId}`);
  }

  // Methods to get current counts for each feature type
  // Optimized to use pagination metadata instead of fetching all data
  async getCurrentCounts(userId: number): Promise<Record<string, number> | ApiError> {
    try {
      const counts: Record<string, number> = {};
      
      // Get counts using pagination metadata (fetch only 1 item per resource to get total count)
      const [accounts, categories, expenses, incomes, debts, goals] = await Promise.allSettled([
        this.accountApi.getAccounts(), // This endpoint doesn't support pagination yet, so we fetch all
        this.categoryApi.getCategoriesPaginated({ page: 1, size: 1, flat: true }),
        this.expenseApi.getExpensesPaginated({ page: 1, size: 1 }),
        this.incomeApi.getIncomesPaginated({ page: 1, size: 1 }),
        this.debtApi.getDebts(), // This endpoint doesn't support pagination yet
        this.goalsApi.getGoals({ page: 1, size: 1 })
      ]);

      // Process results - use pagination metadata when available
      if (accounts.status === 'fulfilled' && !('error' in accounts.value)) {
        counts.accounts = Array.isArray(accounts.value) ? accounts.value.length : 0;
      }
      
      if (categories.status === 'fulfilled' && !('error' in categories.value)) {
        // Use total from pagination metadata
        counts.categories = 'total' in categories.value ? categories.value.total : 0;
      }
      
      if (expenses.status === 'fulfilled' && !('error' in expenses.value)) {
        // Use total from pagination metadata
        counts.expenses = 'total' in expenses.value ? expenses.value.total : 0;
      }
      
      if (incomes.status === 'fulfilled' && !('error' in incomes.value)) {
        // Use total from pagination metadata
        counts.incomes = 'total' in incomes.value ? incomes.value.total : 0;
      }
      
      if (debts.status === 'fulfilled' && !('error' in debts.value)) {
        counts.debts = Array.isArray(debts.value) ? debts.value.length : 0;
      }
      
      if (goals.status === 'fulfilled' && !('error' in goals.value)) {
        // Use total from pagination metadata
        counts.goals = 'total' in goals.value ? goals.value.total : 0;
      }

      // For recurring, we'll need to implement this when recurring API is available
      counts.recurring = 0; // Placeholder

      return counts;
    } catch (error) {
      return { error: 'Failed to get current counts' };
    }
  }
}
